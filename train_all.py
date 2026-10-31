"""train_all.py -- every seed of Phase D's pair, on one machine.

    python train_all.py --engine b58 --device cpu --road wideair --seeds 0-4 --steps 1080000 --jobs 10 --keep-buffer --out runs/wideair_dt1
                                                       # X2 (11 Oct): 5 seeds a side, 1200 episodes each
    python train_all.py --engine b58 --device cpu --road extremes --seeds 0-22 --no-resume --out runs/x2   # X1's design, a new experiment
    python train_all.py --engine b58 --device cpu --road extremes   # X1 itself (CLOSED since 9 Oct: runs/extremes_dt1)
    python train_all.py --engine b58 --device cpu --road terrain    # the 29 Sep design (CLOSED: runs/terrain_dt1)
    python train_all.py --engine b58 --device cpu --road extremes --jobs 10 --out runs/x2   # at most ten at once

THE ROAD IS REQUIRED (8 October 2026). Until then this launcher passed no
--road and no --dt and leaned on train.py's defaults, which is the trap AUDIT2.md
Part 3 names: a default that selects an experiment. Both are passed explicitly.
THE ENGINE IS REQUIRED TOO (20 October 2026, decision 24), and passed on: train.py
has no default plant.
THE DEVICE IS REQUIRED TOO (21 October 2026, the review of benchmark_training.py),
cpu or cuda, and passed on. Without it train.py took "auto", which is CUDA
wherever the installed torch sees a GPU, whatever was measured or preregistered;
CPU and CUDA train different agents from one seed, so one experiment trains on
one device type (rule 3, decision 32), the one benchmark_training.py chose, and
train.py refuses a device torch cannot give. X1 and X2 trained on the CPU (all
56 of their config.json files: device cpu). With --device cuda every run gets
CUBLAS_WORKSPACE_CONFIG set to check_training_device.CUBLAS_WORKSPACE, the one
value train.py accepts on CUDA; that constant says why it is set.

Each run is `python train.py --engine E --road R --dt 1 --steps STEPS --seed S
--device D --out OUT [--no-preview] [--no-resume]` in its own process with
OMP_NUM_THREADS=1, logging to OUT/log_<tag>.txt.

THE FOUR-ENGINE TEST (31 October 2026; rows 102, 116-118 of results/
VALIDATION_DECISIONS.md), on --road four_engine:

    python train_all.py --engine E --device D --road four_engine --third-arm --recipe29
                        --roads-record results/EPA_ROADS/roads.json --seeds ... --steps 450000 --out ...

--third-arm trains THREE arms per seed instead of the pair: a sighted agent at H = r x
tau for each ratio the roads record holds (row 102: r = 0.5 and 1.5, the same on every
engine), tau the engine's frozen time constant as the record holds it (written once at
the draw by roads_ceiling's one definition), and one blinded agent, which serves both
ratios (row 117). Their run directories are sighted_r0.5_seed<S>, sighted_r1.5_seed<S>
and blind_seed<S>; each sighted run gets --horizon-ratio r and --roads-record, and
train.py computes H itself (four_engine_roads.horizon_s, one definition). H BECOMES AN
ENVIRONMENT PARAMETER ONLY WITH ROW 94'S PLANT COMMIT (row 117; ORDER step 14): until
then every H but today's 30 s is refused, so --third-arm prints each engine's H and the
step each preview sample falls on, and stops before it makes a directory or starts a
run. The H refusal it prints is train.py's (four_engine_roads.preview_h_problem), and
lifting it there opens both. --ratios R [R ...] trains the third arm at some of the
record's ratios only (decision 29's pilot under A+G is the blinded arm and r = 1.5, row
112), each refused unless the record holds it.
--recipe29 passes decision 29's recipe to every run (row 118): --lr-schedule last-third,
--scored-share and --checkpoint-average 50000 (training_recipe.DECISION_29_WINDOW).
Without --third-arm and --recipe29 every command is the one this file built before.

WHAT THE PLANT COMMIT ADDS HERE (row 94's commit, ORDER step 14; rows 113 (5), 117). The
team chose the reward without the knock term for this test (row 113 (5); ORDER's status
line: "A+G, the reward without the knock term"), and row 118 puts it behind an
environment option whose default is X1's, knock in. That option does not exist before
the plant commit (engine_env.py is frozen until the last redraw is recorded), so nothing
here can pass it yet. When it lands, every four-engine command must pass it explicitly,
as --recipe29 passes the recipe, with a test that the commands carry it; the
preregistration's commands name it, and so do schema 4's FATAL fields (with preview_h_s
and the train and score backends, row 117). Until then a four-engine run trains on the
reward with the knock term, which is X1's and not the test's.

CRASHES. Without --no-resume, re-running resumes every run from its last
checkpoint, so a closed laptop costs at most the 10 000 steps since the last
one -- but SAC.load does not restore the replay buffer, so a resumed agent is
not the agent an unbroken run would have trained. With --no-resume (C4's crash
rule, and the 8 October preregistration's), a run that died is moved aside to
OUT/<tag>.crashed<N> -- kept, never deleted -- and trained again from step 0;
on the CPU with one thread a fresh run from the same seed is the same agent
(C4 retraced its D2 twins bit for bit). With --keep-buffer (X2's rule, for runs
too long to restart from 0) a crashed run resumes from its last checkpoint WITH
the replay buffer saved beside it: close to an unbroken run, not equal to it
(train.py's docstring says what still differs).

WHY ONE PROCESS PER RUN, ON THE CPU (29 September 2026, measured): a step is
84 % plant, which is numpy on one core, so the runs parallelise across cores
and not across anything else; see train.py's docstring for the timing. On
19 September ten runs sharing the 20-thread team laptop ran about 4.5 steps/s
each, against 13.7 alone.

Then score and document them:

    python record_agents.py runs/<road>_dt1
"""
import argparse
import json
import os
import subprocess
import sys
import time

import engines
import fingerprint as FP
import four_engine_roads as FER
import training_recipe as TR

HERE = os.path.dirname(os.path.abspath(__file__))


def seeds(spec):
    """'0-19' or '0 1 2' -> a list of ints."""
    out = []
    for part in spec:
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    return out


def move_crashed(outdir):
    """A --no-resume run that died: moved aside, kept, and named for what it is."""
    if not os.path.isdir(outdir) or os.path.exists(os.path.join(outdir, "final.zip")):
        return None
    if FP.running_pid(outdir):
        raise SystemExit(f"{outdir} is being trained right now; stop that first.")
    try:
        with open(os.path.join(outdir, "meta.json"), encoding="utf-8") as fh:
            if json.load(fh).get("resume_allowed") is not False:
                return None
    except (OSError, ValueError):
        pass
    n = 1
    while os.path.exists(f"{outdir}.crashed{n}"):
        n += 1
    os.rename(outdir, f"{outdir}.crashed{n}")
    return f"{outdir}.crashed{n}"


def ratios(a, record):
    """The third arm's ratios: --ratios if given (each one of the record's, checked by
    check_four_engine), otherwise every ratio the roads record holds."""
    chosen = getattr(a, "ratios", None)
    return [float(r) for r in (chosen if chosen else record["ratios"])]


def arms(a, record):
    """[(seed, use_preview, ratio)] in launch order: every seed's pair, sighted then
    blind (ratio None), or with --third-arm a sighted agent at each of the third arm's
    ratios (ratios()) and one blinded agent (row 117)."""
    if not a.third_arm:
        return [(s, not blind, None) for s in a.seeds for blind in (False, True)]
    return [(s, True, r) for s in a.seeds for r in ratios(a, record)] + \
        [(s, False, None) for s in a.seeds]


def commands(a, record):
    """[(tag, train.py command)] for every run. Without --third-arm and --recipe29
    each command is the one this file built before 31 October 2026, argument for
    argument (test_four_engine_training.py holds them equal)."""
    out = []
    for s, sighted, ratio in arms(a, record):
        tag = FER.run_tag(s, use_preview=sighted, ratio=ratio)
        cmd = [sys.executable, "train.py", "--engine", a.engine, "--road", a.road, "--dt", f"{a.dt:g}",
               "--steps", str(a.steps), "--seed", str(s), "--device", a.device, "--out", a.out]
        if not sighted:
            cmd.append("--no-preview")
        if ratio is not None:
            cmd += ["--horizon-ratio", repr(ratio)]
        if a.recipe29:
            cmd += ["--lr-schedule", "last-third", "--scored-share",
                    "--checkpoint-average", str(TR.DECISION_29_WINDOW)]
        if ratio is not None or a.recipe29:
            cmd += ["--roads-record", record["path"]]
        if a.no_resume:
            cmd.append("--no-resume")
        if a.keep_buffer:
            cmd.append("--keep-buffer")
        out.append((tag, cmd))
    return out


def third_arm_problems(a, record):
    """The third arm's H on this engine, printed, and why train.py would refuse it
    (four_engine_roads.preview_h_problem): (lines, problems)."""
    lines, problems = [f"the third arm on {a.engine} (rows 102, 117), tau from {record['path']} "
                       f"({record['seed_kind']}):"], []
    for r in ratios(a, record):
        h = FER.horizon_s(record, a.engine, r)
        lines.append(f"  r = {float(r):g}: tau {h / float(r):.4f} s, H = {h:.4f} s, preview samples at steps "
                     f"{FER.preview_steps(h, dt=a.dt)} (dt {a.dt:g} s)")
        p = FER.preview_h_problem(h)
        if p:
            problems.append(f"r = {float(r):g}: {p}")
    lines.append("  blinded: one arm for both ratios, no H (row 117)")
    return lines, problems


def check_four_engine(a):
    """--third-arm, --recipe29 and --roads-record, refused before any directory or run
    exists. Returns the roads record read_roads_record reads, or None."""
    needs = a.third_arm or a.recipe29
    if a.road == "four_engine":
        problem = FER.reserved_seed_problem(a.seeds)
        if problem:
            raise SystemExit(f"REFUSING --seeds on the four-engine roads: {problem}.")
    if a.roads_record is not None and not needs:
        raise SystemExit("REFUSING: --roads-record without --third-arm or --recipe29: no run would read it.")
    if getattr(a, "ratios", None) and not a.third_arm:
        raise SystemExit("REFUSING: --ratios without --third-arm: only the third arm trains at r x tau.")
    if not needs:
        return None
    if a.road != "four_engine":
        raise SystemExit(f"REFUSING: --third-arm and --recipe29 are the four-engine test's (--road four_engine; "
                         f"rows 116-118), not --road {a.road}'s.")
    try:
        record = FER.read_roads_record(a.roads_record)
    except FER.Refused as exc:
        raise SystemExit(f"REFUSING: {exc}.")
    if record["seed_kind"] != "REAL" and FER.inside_repository(os.path.join(HERE, a.out)):
        raise SystemExit(f"REFUSING: {record['path']} is a {record['seed_kind']} roads record and {a.out} lies "
                         "inside the repository: a SYNTHETIC share trains into a temporary folder only.")
    if record["seed_kind"] == "REAL":
        problem = FER.real_record_problem(record["path"])
        if problem:
            raise SystemExit(f"REFUSING: {problem}.")
    if getattr(a, "ratios", None):
        held = [float(x) for x in record["ratios"]]
        bad = [r for r in a.ratios if float(r) not in held]
        if bad or len(set(a.ratios)) != len(a.ratios):
            raise SystemExit(f"REFUSING --ratios {a.ratios}: each must be one of the roads record's ratios "
                             f"{held} (row 102), once.")
    if a.recipe29:
        try:
            TR.snapshot_steps(a.steps, TR.DECISION_29_WINDOW)
        except ValueError as exc:
            raise SystemExit(f"REFUSING --recipe29: {exc}.")
    if a.third_arm:
        try:
            lines, problems = third_arm_problems(a, record)
        except FER.Refused as exc:
            raise SystemExit(f"REFUSING the third arm: {exc}.")
        print("\n".join(lines))
        if problems:
            raise SystemExit("REFUSING the third arm, before any run starts: " + " | ".join(problems) + ".")
    return record


def main():
    ap = argparse.ArgumentParser()
    # engines.trainable(), not known() (22 October 2026, decision 47), as train.py
    ap.add_argument("--engine", required=True, choices=engines.trainable(),
                    help="the plant every run trains on, passed to train.py (no default; "
                         "engines.trainable(), decision 47)")
    ap.add_argument("--road", required=True, choices=("terrain", "extremes", "wideair", "four_engine"))
    ap.add_argument("--device", required=True, choices=("cpu", "cuda"),
                    help="the device every run trains on, passed to train.py (no default: "
                         "benchmark_training.py chooses it, decision 32; see the docstring)")
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--seeds", nargs="+", default=["0-9"], help="'0-19' or '0 1 2'")
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=None, help="default runs/<road>_dt1")
    ap.add_argument("--no-resume", action="store_true",
                    help="a crash is re-run from step 0, never resumed (see the docstring)")
    ap.add_argument("--keep-buffer", action="store_true",
                    help="each run saves its replay buffer with every checkpoint and a "
                         "crashed run resumes with it (see the docstring)")
    ap.add_argument("--third-arm", action="store_true",
                    help="three arms per seed: sighted at H = r x tau for each ratio of --roads-record, "
                         "and one blinded (rows 102, 117; --road four_engine). Refused until row 94's "
                         "plant commit makes H an environment parameter")
    ap.add_argument("--ratios", nargs="+", type=float, default=None, metavar="R",
                    help="with --third-arm: train the sighted arm at these of the record's ratios only "
                         "(decision 29's pilot under A+G: 1.5, row 112). Default: every ratio it holds")
    ap.add_argument("--recipe29", action="store_true",
                    help="decision 29's recipe for every run: --lr-schedule last-third, --scored-share, "
                         "--checkpoint-average 50000 (row 118; --road four_engine)")
    ap.add_argument("--roads-record", default=None, metavar="PATH",
                    help="the committed roads record (results/EPA_ROADS/roads.json): tau for "
                         "--third-arm, roads_seed for --recipe29")
    a = ap.parse_args()
    if a.keep_buffer and a.no_resume:
        raise SystemExit("--keep-buffer exists for resuming; --no-resume forbids it. Pick one.")
    a.seeds = seeds(a.seeds)
    if a.out is None:
        a.out = os.path.join("runs", f"{a.road}_dt{a.dt:g}".replace(".", "p"))
    record = check_four_engine(a)       # before any directory or run (rows 116-118)

    runs = commands(a, record)
    os.makedirs(os.path.join(HERE, a.out), exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1")
    if a.device == "cuda":
        # train.check_device refuses CUDA without it; one constant for every launcher, and the
        # value benchmark_training.py measured CUDA with
        from check_training_device import CUBLAS_WORKSPACE
        env["CUBLAS_WORKSPACE_CONFIG"] = CUBLAS_WORKSPACE
    queue, live, done = list(runs), {}, []
    t0 = time.time()
    print(f"{len(runs)} runs ({a.engine}, {a.road}, dt {a.dt:g}, {a.device}), {a.steps:,} steps each, "
          f"at most {a.jobs} at once -> {a.out}/")
    while queue or live:
        while queue and len(live) < a.jobs:
            tag, cmd = queue.pop(0)
            if a.no_resume:
                moved = move_crashed(os.path.join(HERE, a.out, tag))
                if moved:
                    print(f"  {tag} had crashed: moved aside to {moved}, training it again from 0")
            log = open(os.path.join(HERE, a.out, f"log_{tag}.txt"), "a")
            live[tag] = (subprocess.Popen(cmd, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT), log)
            print(f"  started {tag}")
        time.sleep(20)
        for tag, (p, log) in list(live.items()):
            if p.poll() is not None:
                log.close()
                done.append((tag, p.returncode))
                del live[tag]
                print(f"  {'finished' if p.returncode == 0 else 'FAILED (exit %d)' % p.returncode} {tag}"
                      f"  after {(time.time() - t0) / 60:.0f} min")
    bad = [t for t, rc in done if rc != 0]
    print(f"\nall done in {(time.time() - t0) / 60:.0f} min; "
          + (f"FAILED: {', '.join(bad)} -- read their logs, then re-run this command"
             + (" (each is moved aside and trained again from 0)" if a.no_resume else " to resume")
             if bad else "every run finished"))
    print("next: python record_agents.py " + a.out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

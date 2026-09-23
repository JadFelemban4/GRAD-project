"""check_c4_start.py — is C4 really Phase D2 with only the budget changed? Run early.

    python check_c4_start.py                               seconds; prints only
    python check_c4_start.py --out results/c4_identity.txt the final pass, kept

Run it about fifteen minutes after launch, when the first checkpoints (10 000
steps) have appeared; again at about eighty; again after the second wave has
started and reached 50 000 steps; and once more, with `--out`, before C4 is
evaluated -- then all 80 checkpoint pairs (16 runs x 10k-50k) exist
(`results/PREREGISTRATION_C4.md` section 9). It needs no GPU and loads no
agent: it reads the zips.

WHAT IT CHECKS, AND WHY EACH ONE CAN FAIL
-----------------------------------------
1. THE CERTIFICATE. Every `runs_c4/<tag>/meta.json` must carry Phase D2's fatal
   fingerprint (plant, scenario, episodes -- `results/PREREGISTRATION_C4.md`
   section 3 pins the three hashes), `steps_requested` 300 000, `--no-resume`,
   and a clean tree -- AND its `git_head` must descend from the commit that
   added `results/PREREGISTRATION_C4.md`. That last check is what makes
   "preregistered before training" something git shows rather than something
   this file asserts: a run started before the preregistration was committed
   cannot pass it.

2. THE BUDGET, from the zip. Every C4 checkpoint must say it belongs to a
   300 000-step run that started at step 0 with a 300 000-slot buffer
   (`fingerprint.model_budget`). A resumed D2 agent would say 50 000 slots and
   a non-zero start.

3. THE IDENTITY -- a prediction, and the reason this file is worth having.
   C4 changes ONE thing from D2: `--steps`. The seed, the road stream, the
   preference draws, the network, the learning rate and the code path are the
   same, and a buffer that has not filled does not change what is sampled
   (`prove_buffer.py`: largest weight difference 0 on this machine). So up to
   50 000 steps a C4 run should retrace its D2 twin EXACTLY, and each
   `ckpt_<n>_steps.zip` should hold the same weights as D2's. One probe
   (sighted seed 0, 10 000 steps, 23 September) did.

   * IDENTICAL: C4's agents ARE D2's agents, trained longer, up to 50 000
     steps -- beyond that there is no twin, and it rests on the code path.
   * DIFFERENT: something besides the budget moved -- GPU non-determinism
     under a different load, a library, a code path. The preregistration
     declares what follows (section 3a): C4 continues, because it is still
     D2's design at a larger budget, but the difference is recorded in 6a and
     the two experiments can no longer be read as the same agents at two ages.

   It compares the POLICY weights (actor, critic, target critic) tensor by
   tensor, and only for checkpoints whose own budget passed check 2. It uses
   checkpoints only: D2's `final.zip` is one gradient step past its
   `ckpt_50000_steps.zip` (`_n_updates` 49 900 against 49 899), so C4's
   checkpoint against D2's final would differ by construction.
"""
import argparse
import io
import os
import re
import subprocess
import sys
import time
import zipfile

import fingerprint as FP

HERE = os.path.dirname(os.path.abspath(__file__))
C4_STEPS = 300_000
TAGS = [f"{arm}_seed{s}" for s in range(8) for arm in ("sighted", "blind")]
PREREG = "results/PREREGISTRATION_C4.md"

# results/PREREGISTRATION_C4.md section 3 -- the same values D2 pinned.
PINS = {"plant_sha": "b5a3069f32a83754", "episodes_sha": "1c5d49852290d27c",
        "road_sha": "1a29dc46db24f233"}


def weights(zip_path):
    """The policy state_dict from an SB3 zip, on the CPU."""
    import torch
    with zipfile.ZipFile(zip_path) as z:
        return torch.load(io.BytesIO(z.read("policy.pth")), map_location="cpu",
                          weights_only=True)


def max_diff(a, b):
    if set(a) != set(b):
        return float("inf")
    return max(float((a[k].float() - b[k].float()).abs().max()) for k in a)


def git(*args):
    try:
        r = subprocess.run(("git",) + args, cwd=HERE, capture_output=True,
                           text=True, timeout=20)
        return r
    except (OSError, subprocess.SubprocessError):
        return None


def prereg_commit():
    """The commit that ADDED the preregistration, or None if it is not committed."""
    r = git("log", "--diff-filter=A", "--format=%H", "--", PREREG)
    if r is None or r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.strip().splitlines()[-1]


def descends(head, base):
    r = git("merge-base", "--is-ancestor", base, head)
    return r is not None and r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?", default="runs_c4")
    ap.add_argument("--out", default=None,
                    help="also write the report (the final pass: results/"
                         "c4_identity.txt). Never overwritten.")
    a = ap.parse_args()
    if a.out and os.path.exists(os.path.join(HERE, a.out)):
        raise SystemExit(f"{a.out} exists -- it is never overwritten")
    c4 = os.path.join(HERE, a.runs)
    d2 = os.path.join(HERE, "runs_d2")
    if not os.path.isdir(c4):
        raise SystemExit(f"{c4} does not exist yet")
    ref = FP.read(os.path.join(d2, "sighted_seed0", "meta.json"))
    base = prereg_commit()
    lines, problems, busy = [], [], []
    compared = identical = 0

    def say(s=""):
        print(s)
        lines.append(s)

    say(f"C4 START CHECK -- {a.runs}/ against runs_d2/, "
        f"{time.strftime('%Y-%m-%d %H:%M')}")
    say(f"preregistration committed in {base[:7] if base else 'NOT COMMITTED'}")
    say(f"{'agent':<16}{'meta':<9}{'budget':<9}identity with runs_d2/, per checkpoint")
    say("-" * 78)
    for tag in TAGS:
        d = os.path.join(c4, tag)
        meta = FP.read(os.path.join(d, "meta.json")) if os.path.isdir(d) else None
        if not os.path.isdir(d):
            say(f"{tag:<16}not started")
            continue
        if meta is None:
            say(f"{tag:<16}starting (no meta.json yet)")
            continue
        head = meta.get("git_head") or ""
        m_ok = (not FP.compare(meta, ref)
                and meta.get("steps_requested") == C4_STEPS
                and meta.get("resume_allowed") is False
                and meta.get("git_dirty") is False
                and meta.get("plant_sha") == PINS["plant_sha"]
                and meta.get("episodes_sha") == PINS["episodes_sha"]
                and (meta.get("scenario") or {}).get("road_sha") == PINS["road_sha"]
                and base is not None and descends(head, base))
        if not m_ok:
            problems.append(
                f"{tag}: meta.json is not a clean C4 certificate (steps "
                f"{meta.get('steps_requested')}, no-resume "
                f"{meta.get('resume_allowed') is False}, dirty "
                f"{meta.get('git_dirty')}, git_head {head[:7]} after the "
                f"preregistration {bool(base) and descends(head, base)}, "
                f"fatal diff {FP.compare(meta, ref)})")
        ckpts = sorted(int(m.group(1)) for f in os.listdir(d)
                       if (m := re.match(r"ckpt_(\d+)_steps\.zip$", f)))
        b_ok, marks = True, []
        for n in ckpts:
            p = os.path.join(d, f"ckpt_{n}_steps.zip")
            # A checkpoint written in the last few seconds may still be being
            # written (stable-baselines3 saves in place): skip it this pass.
            if time.time() - os.path.getmtime(p) < 10:
                busy.append(f"{tag} ckpt {n}")
                continue
            b = FP.model_budget(p)
            ok = (b is not None and b["num_timesteps"] == n
                  and b["total_timesteps"] == C4_STEPS
                  and b["num_timesteps_at_start"] == 0
                  and b["buffer_size"] == C4_STEPS)
            if not ok:
                b_ok = False
                problems.append(f"{tag} ckpt {n}: {FP.format_budget(b)}")
                continue          # not a C4 checkpoint: it says nothing about identity
            twin = os.path.join(d2, tag, f"ckpt_{n}_steps.zip")
            if not os.path.exists(twin):
                continue          # D2 stopped at 50 000; beyond it there is no twin
            try:
                diff = max_diff(weights(p), weights(twin))
            except (zipfile.BadZipFile, KeyError, RuntimeError, OSError):
                busy.append(f"{tag} ckpt {n}")
                continue
            compared += 1
            identical += diff == 0.0
            marks.append(f"{n // 1000}k " + ("=" if diff == 0.0 else f"DIFF {diff:.1e}"))
        say(f"{tag:<16}{'ok' if m_ok else 'BAD':<9}{'ok' if b_ok else 'BAD':<9}"
            + ("  ".join(marks) if marks else "no checkpoint compared yet"))
    say("-" * 78)
    say(f"IDENTITY compared {compared} identical {identical}")
    if compared and identical == compared:
        say("IDENTICAL so far: these C4 runs are retracing their D2 twins exactly.")
    elif compared:
        say("NOT IDENTICAL: something besides the budget differs from D2. C4")
        say("continues (PREREGISTRATION_C4.md section 3a) -- RECORD THIS in its")
        say("run log, section 6a, before reading any C4 result.")
    if busy:
        say("being written, skipped this pass (re-run): " + ", ".join(busy))
    for p in problems:
        say("!! " + p)
    if a.out:
        with open(os.path.join(HERE, a.out), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"written to {a.out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

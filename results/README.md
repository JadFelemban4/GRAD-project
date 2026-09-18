# results/ — what the runs actually printed, kept because `runs/` is gitignored

The trained policies themselves are 3 MB each and stay out of git. What is kept
here is the evidence: the learning curves as CSV, and the evaluation table
exactly as `evaluate.py` printed it.

Regenerate any of it with:

```bash
python train.py --steps 50000 --seed 0                 # ~63 min
python train.py --steps 50000 --seed 0 --no-preview     # ~63 min
python evaluate.py runs/sighted_seed0 runs/blind_seed0  # ~15 min
```

## phase_d_seed0.txt — THE FIRST MEASURED PREVIEW ADVANTAGE

**One seed against one seed. Phase D needs five of each. Do not quote it yet.**

The number that matters is the last line: **sighted +11.7 points over blinded**,
from a proper ablation — two agents trained identically, differing only in
whether the preview channel carried the road ahead or zeros.

Read the caveats in `CLAUDE.md` before repeating the figure. The short version:
the worst episode goes the other way (blind 336.9 against sighted 378.8), the
sighted agent burns 6.6 % more fuel for its advantage, and n = 1.

## curve_*.csv — the training curves, and why they prove nothing

`episode, return, length`. **These returns are not comparable to each other.**
`SupervisoryTunerEnv.reset()` draws a fresh preference vector every episode, so
each row is scored with a different ruler. Seed 0 sighted ranges from −506.4 to
+643.6 over eleven episodes, and its single best episode is in the FIRST five.

`train.py` prints "first 5 → last 5, the curve improved" from these. With that
spread and eleven samples, that comparison is the weight draw, not learning.
**The evaluation protocol exists because of this**, and it is the only thing
that settles whether a policy is better: twenty episodes with the weights
pinned, identical for every policy.

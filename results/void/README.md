# `results/void/` — result files that are NOT results

Kept because `AUDIT2.md` C2-1 asks for them to be kept, and because deleting
the evidence for a finding is how the finding comes back.

## `phase_d_seed0_SIXSPEED_VOID.txt`

The file that said **+11.7 points** and carried the line *"THE ABLATION. This
is the project's result."*

It is not a result, for a reason nothing in the file itself can show: the two
agents behind it were trained on **an invented six-speed gearbox** that commit
`27e720c` replaced with the car's real ZF 8HP51 **seven hours later**. Its
header —

```
scenario: 12 % at 130 km/h, 42 C, 720 s, dt 1.0
```

— is a hardcoded string that was **byte-identical on both plants**. That is the
whole of C2-1: the number was wrong and the file could not tell anyone.

Re-scoring the same pair on the corrected plant gave +7.5, which is not a result
either, because those agents had never seen the plant they were being scored on.

**Both numbers are void. Do not quote either.**

## What replaced it

`results/phase_d_seed0.txt` … `phase_d_seed7.txt`, produced 21–22 September
2026 from sixteen agents trained on the current plant, under
`results/PREREGISTRATION.md`, which was committed before any of them started.

Every one of those files opens with a **plant fingerprint block**, and
`evaluate.py` refuses a model whose fingerprint disagrees with the tree it is
run on. The failure this directory records cannot happen silently again — that
is what the fingerprint is for, and this file is what it is for.

Run `python analyse_phase_d.py` for the preregistered test over all eight seeds.

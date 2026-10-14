---
paths:
  - "train.py"
  - "train_all.py"
  - "evaluate.py"
  - "run_phase_d.py"
  - "fingerprint.py"
  - "analyse_*.py"
  - "results/**"
---

# Training, scoring and analysis

Loaded when a training, scoring or analysis file is read or edited. Before any
training: CLAUDE.md's Training gate and its rules for an experiment that will
be reported. Neither is copied here.

- The twenty frozen episodes in `evaluate.py` never change. Changing the test
  set after seeing a result is the one mistake this project cannot recover from.
- After its result, a preregistered experiment adds no seed and switches no
  tail. More seeds is a new experiment, with its own preregistration, and both
  are reported.
- `train.py` writes `meta.json`, the plant fingerprint, before the first step,
  and refuses a resume whose plant, `dt`, device or budget differs ("A RESUME IS
  NOT A LONGER RUN" in `train.py`). A new experiment gets a new `--out`; the
  closed run directories are listed in `train.py`'s help.
- `evaluate.py` refuses a model whose `meta.json` differs from the live plant.
- Until drive C, report every result with and without the knock term
  (Training gate, item 3).

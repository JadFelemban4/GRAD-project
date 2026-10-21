"""thresholds -- the steps of engine_thresholds.py, one module per step.

The validation contract of decision 35 (results/ENGINE_THRESHOLDS.md and .json) is
written by `python engine_thresholds.py`; its docstring says what every step computes and
reads. These modules hold the code, in the order the steps run:

  split.py            1. the held-out split, from the EPA tables' structure alone
  alpha_nodes.py      2. which ALPHA curve nodes sit on held-out rows
  b58_propagation.py  3. the B58's sensitivities, its ECU in the loop
  knee_shift.py       4. how far d moves when the turbine knee moves (committed records)
  ecu_shift.py        5. the B58 ECU's boosted output shifted, one run per process
  contract.py         6. every R, from the MEI, R1 and steps 1-5: the JSON
  document.py         7. the .md, from document_template.md and the contract

None of them compares a model with an EPA torque, fuel or turbine-inlet-temperature value,
fits anything or calibrates anything. Steps 3-5 run the B58 plant only.
"""

# results/EPA_TIT_CAP — the Ford's TIT cap (row 105)

Row 105's record, for decision 62's TIT-cap row and row 124. `ford_27tt.json` is written once
by `python -B tit_cap.py compute --engine ford_27tt`, from committed, clean code (schema
`epa-tit-cap/2`), and never overwritten.

- `cap.tit_k` is the highest TIT on the Ford's calibration Final rows: decision 62's first
  option, row 105's rule. `sensitivity_egt_limit.tit_k` is the spec's `egt_limit_k` (ASSUMED),
  the second sensitivity row. Neither decides a label (row 105). Both are re-scored by row
  115 (d).
- The `audit` block covers the whole command. `before_the_audit` lists what the standard-library
  prelude saw before the first project import. `opened`, `subprocesses`, `refused_by_audit` and
  `outside_allowlist` list the rest, up to the write.
- `provenance` carries plant_sha, engine_sha, the code's sha_text over `epa_freeze.CODE_HASHED`,
  and freeze.json's contract block. `git` names the commit the record was written from.
- The ECU that applies either cap is `tit_cap_ecu.capped`. When no λ in bounds holds the cap, it
  returns the λ of least model TIT in [lam_floor, λ_ECU] (row 124 (1)). The cap holds the model
  TIT at the ECU's own operating point, not the realised one (row 124 (2)).
- Row 115 reads the cap through `tit_cap_ecu.cap_from_record(..., committed=True)`, which refuses
  a stale, spoiled or uncommitted record. The patch is per process: a pool worker enters
  `capped()` itself.

The numbers belong to the record, not to this file.

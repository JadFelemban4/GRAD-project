# Step 3 on the training device, 2 November 2026

ORDER step 3 (`tools/device_step3.sh`), run by Jad on his PC, the training device, at the clean,
pushed commit `b2151af`. Every other file in this folder is the step's output, copied from the
archive Jad sent on 5 November (`2026-11-02_step3.tar.gz`, sha256
`950fedd4122ecbfae9f4f7693d04e6a6bfad414be98bcf422a364db759b0745f`). They are not edited. Git stores
them with its line-ending normalisation, so a checkout's bytes can differ from the archive's in line
endings only.

Row 135 of `results/VALIDATION_DECISIONS.md` (section O) reads them. The device and the number of
runs at once come from `A5_bench_merged.json` (its `.txt` prints the RECOMMENDATION line). The
seed count n does not come from here: it comes from B1 at ORDER step 18 (row 114).

| file | what it is |
|---|---|
| `A0_commit.txt`, `A0_status.txt` | the commit, and `git status --porcelain` (empty: a clean tree) |
| `A_machine.txt`, `A2_versions.txt` | the machine, and the interpreter and package versions |
| `A3_*` | the CPU series: the self-test, the dry run, the benchmark (`.json` and its `.txt`) |
| `A4_*` | the CUDA series: the torch build, the dry run, the benchmark |
| `A5_bench_merged.*` | the merge of the two series, with its recommendation |
| `A6_summary.txt` | the step's own summary |
| `step3_log.txt`, `keep_awake.log` | the whole session's log, and the keep-awake loop's |

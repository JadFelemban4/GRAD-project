#!/usr/bin/env bash
# run_l8.sh -- certificate level L8 (results/B58_IDENTITY.md, item 3.6.20) on the training device: 600 SAC
# steps, seed 0, CPU, one thread, through train.py in the candidate tree and in the certificate's reference
# tree (git archive cf43fbb), with the wrapper and the perturbed controls; every pair compared, each run's
# identity read from its meta.json, a verdict, then the run directories deleted (an identity test, not an
# experiment).
#
#   bash tools/run_l8.sh --cand <repository> --py <python> --out <new folder> [--dry-run]
#
#   --cand     the candidate: the clone at the commit under test (decision 61: the training device's)
#   --py       the interpreter of the lock's environment (Windows: .venv/Scripts/python.exe; Linux:
#              .venv/bin/python); both trees run in it, as the certificate's two trees ran in one
#   --out      a folder that does not exist yet, or is empty, outside the candidate; the script makes
#              OUT/ref, OUT/tools and OUT/L8 in it and leaves the logs, the comparisons and the verdict
#   --dry-run  everything a real run does before it trains (OUT, ref/ checked against the archive,
#              tools/ from the tarball), then each of the eleven commands with --help appended: the two
#              trees, the interpreter, the wrapper and every path are exercised, and nothing trains
#
# WHY THIS FILE (row 118 of results/VALIDATION_DECISIONS.md; ORDER_TO_TRAINING.md step 7). The certificate's
# own run_l8.sh, inside results/B58_IDENTITY/certificate_tools.tar.gz, defaults PY and CAND to the team
# laptop's paths, converts paths with cygpath (Git Bash only), and writes into $S/L8 and reads $S/ref
# without creating either. That tarball is the certificate's record and is left as it was made. This one:
#   * takes the candidate, the interpreter and the output folder as required arguments: no path defaults;
#   * converts no path with cygpath: a folder's native form is `pwd -W` under Git Bash and `pwd` on Linux,
#     so it runs under Git Bash on Windows and under bash on Linux;
#   * makes OUT/ref (git archive of cf43fbb from the candidate's own repository, checked with tar
#     --compare, as the certificate checked S/ref) and OUT/L8 itself;
#   * takes l8_compare.py and l8_perturbed.py out of the tarball, byte for byte, into OUT/tools (each
#     sha256 recorded), so the comparison and the wrapper are the certificate's own;
#   * runs what the certificate's run_l8.sh and run_l8_review.sh ran (both are in the tarball): the three
#     pairs, the wrapper alone, one ulp on car.mass and on thermal.c_turb, and the relative steps 1e-9 and
#     1e-6 on car.mass; then every comparison and each run's identity.
#
# THE VERDICT. L8 PASSES when every run exits 0, the three pairs (extremes sighted, extremes blind, wideair
# sighted) and the wrapper alone read IDENTICAL TRAINING, and both relative-step controls read NOT
# IDENTICAL: a comparison that cannot see a plant difference proves nothing (mistake 12). One ulp on
# car.mass or on thermal.c_turb gave identical weights in build step 1's L8 ("the network learns from
# float32", STATE_HISTORY.md, its L8 row), so those two are printed and not judged. Every comparison is
# judged on the verdict l8_compare.py prints together with its exit code (cmp8): one that printed none,
# a traceback among them, is ERROR, and an ERROR fails L8 whatever was expected of it.
#
# WHERE ITS OUTPUT GOES: OUT, outside the repository. What L8 leaves (OUT/L8: the logs, _status.txt,
# provenance.txt, compare_*.txt, the cmp/*.json and run_identities.json) is what B1 records
# (docs/build_step_2/DEVICE_RUNBOOK.md).
set -u

REF_COMMIT=cf43fbb      # the certificate's reference tree: results/B58_IDENTITY.md, "code cf43fbb ... in S/ref"
TARBALL_REL=results/B58_IDENTITY/certificate_tools.tar.gz
TOOLS=(tools/l8_compare.py tools/l8_perturbed.py)

die() { echo "run_l8.sh: $*" >&2; exit 2; }
usage() { sed -n '8,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

CAND= PY= OUT= DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --cand) CAND=${2-}; shift 2 || die "--cand needs a folder" ;;
    --py) PY=${2-}; shift 2 || die "--py needs an interpreter" ;;
    --out) OUT=${2-}; shift 2 || die "--out needs a folder" ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument $1 (--help)" ;;
  esac
done
[ -n "$CAND" ] && [ -n "$PY" ] && [ -n "$OUT" ] || { usage >&2; die "--cand, --py and --out are required"; }

native() {   # native <existing folder>: its form for a native program (Git Bash: pwd -W; Linux: pwd)
  (cd "$1" && { pwd -W 2>/dev/null || pwd; })
}

[ -d "$CAND" ] || die "--cand $CAND is not a folder"
CAND_SH=$(cd "$CAND" && pwd) && CAND_PY=$(native "$CAND") || die "cannot enter $CAND"
TOP=$(git -C "$CAND_SH" rev-parse --show-toplevel 2>/dev/null) || die "--cand $CAND is not a git repository"
[ "$(cd "$TOP" && pwd)" = "$CAND_SH" ] || die "--cand must be the repository's top folder ($TOP)"
[ -f "$CAND_SH/train.py" ] && [ -f "$CAND_SH/$TARBALL_REL" ] || die "$CAND has no train.py or no $TARBALL_REL"
git -C "$CAND_SH" cat-file -e "$REF_COMMIT^{commit}" 2>/dev/null \
  || die "the candidate's repository has no commit $REF_COMMIT (the certificate's reference): fetch it first"
"$PY" -c "import sys" 2>/dev/null || die "--py $PY does not run"

if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  die "--out $OUT exists and is not empty: give L8 a new folder"
fi
mkdir -p "$OUT" || die "cannot make $OUT"
OUT_SH=$(cd "$OUT" && pwd) && OUT_PY=$(native "$OUT") || die "cannot enter $OUT"
case "$OUT_SH/" in "$CAND_SH"/*) rmdir "$OUT_SH" 2>/dev/null; die "--out lies inside the candidate: put it outside the repository" ;; esac
mkdir -p "$OUT_SH/ref" "$OUT_SH/tools" "$OUT_SH/L8/cmp" || die "cannot make ref/, tools/ and L8/ in $OUT"
# PYTHONDONTWRITEBYTECODE: no __pycache__ left in either tree (the review of 31 October 2026, R0-4); it
# changes no trained bit. -I ignores every PYTHON* variable, this one included, so the two tools run under
# -I (ctl, cmp8) are given -B as well: without it l8_perturbed.py, which imports engines and train from the
# candidate, wrote twelve .pyc files into the repository's __pycache__ (MEASURED, the last check of
# 31 October 2026: test_device_gate.RunL8.test_a_dry_run alone, before the -B)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
L8=$OUT_SH/L8

# the reference tree, as the certificate made S/ref, and checked as it was (tar --compare; mode, owner and
# time lines left out, as its prep record left them out)
git -C "$CAND_SH" archive "$REF_COMMIT" | tar -x -f - -C "$OUT_SH/ref" || die "git archive $REF_COMMIT did not extract"
git -C "$CAND_SH" archive "$REF_COMMIT" | tar -d -f - -C "$OUT_SH/ref" 2>&1 \
  | grep -v -E 'Mode differs|Uid differs|Gid differs|Mod time differs' > "$L8/ref_compare.txt"
[ -s "$L8/ref_compare.txt" ] && die "OUT/ref is not git archive $REF_COMMIT: see $L8/ref_compare.txt"

# the certificate's two tools, byte for byte (a relative path: GNU tar reads "C:/..." as a remote host)
for t in "${TOOLS[@]}"; do
  (cd "$CAND_SH" && tar -xOzf "$TARBALL_REL" "$t") > "$OUT_SH/$t" || die "$t is not in $TARBALL_REL"
done
{
  echo "candidate      $CAND_PY"
  echo "commit         $(git -C "$CAND_SH" rev-parse HEAD)"
  echo "dirty files    $(git -C "$CAND_SH" status --porcelain | wc -l)"
  echo "reference      $REF_COMMIT ($(git -C "$CAND_SH" rev-parse "$REF_COMMIT^{commit}")), OUT/ref"
  echo "interpreter    $PY ($("$PY" -c 'import platform; print(platform.python_version(), platform.platform())'))"
  echo "tarball        $(cd "$CAND_SH" && sha256sum "$TARBALL_REL")"
  for t in "${TOOLS[@]}"; do echo "tool           $(cd "$OUT_SH" && sha256sum "$t")"; done
  echo "dry run        $DRY"
} > "$L8/provenance.txt"
(cd "$CAND_SH" && "$PY" check_training_device.py > "$L8/versions.txt" 2>&1)
echo "versions (recorded, not required here): $(tail -n 1 "$L8/versions.txt")"

COMMON=(--steps 600 --seed 0 --device cpu)
HELP=()
[ "$DRY" = 1 ] && HELP=(--help)
run() {   # run <name> <folder> <command...>: in the background, its log and its exit status kept
  local name=$1 dir=$2; shift 2
  ( cd "$dir" && s=$(date +%s) && "$@" "${HELP[@]}" > "$L8/$name.log" 2>&1
    echo "$? $(( $(date +%s) - s )) $name" >> "$L8/_status.txt" ) &
}
ctl() {   # ctl <name> <perturbation>: the candidate's train.py through the certificate's wrapper
  run "$1" "$CAND_SH" "$PY" -I -B "$OUT_PY/tools/l8_perturbed.py" "$CAND_PY" "$2" --engine b58 "${COMMON[@]}" \
    --road extremes --out "$OUT_PY/L8/$1"
}
: > "$L8/_status.txt"
run cand_extremes_sighted "$CAND_SH" "$PY" train.py --engine b58 "${COMMON[@]}" --road extremes --out "$OUT_PY/L8/cand_extremes"
run ref_extremes_sighted "$OUT_SH/ref" "$PY" train.py "${COMMON[@]}" --road extremes --out "$OUT_PY/L8/ref_extremes"
run cand_extremes_blind "$CAND_SH" "$PY" train.py --engine b58 "${COMMON[@]}" --road extremes --no-preview --out "$OUT_PY/L8/cand_extremes"
run ref_extremes_blind "$OUT_SH/ref" "$PY" train.py "${COMMON[@]}" --road extremes --no-preview --out "$OUT_PY/L8/ref_extremes"
wait
run cand_wideair_sighted "$CAND_SH" "$PY" train.py --engine b58 "${COMMON[@]}" --road wideair --out "$OUT_PY/L8/cand_wideair"
run ref_wideair_sighted "$OUT_SH/ref" "$PY" train.py "${COMMON[@]}" --road wideair --out "$OUT_PY/L8/ref_wideair"
ctl ctl_none none
ctl ctl_mass car.mass
ctl ctl_cturb thermal.c_turb
wait
ctl ctl_mass1e-9 car.mass:1e-9
ctl ctl_mass1e-6 car.mass:1e-6
wait
echo "runs (exit code, seconds, name):"
sed 's/^/  /' "$L8/_status.txt"
FAILED=$(awk '$1 != 0' "$L8/_status.txt" | wc -l)
NRUNS=$(wc -l < "$L8/_status.txt")

if [ "$DRY" = 1 ]; then
  echo "DRY RUN: $NRUNS commands ran with --help appended, $FAILED did not exit 0; nothing trained, nothing compared."
  echo "  OUT/ref is git archive $REF_COMMIT (tar --compare), OUT/tools holds the tarball's two tools; $L8/provenance.txt"
  [ "$FAILED" = 0 ] && [ "$NRUNS" = 11 ] && exit 0 || exit 1
fi

cmp8() {   # cmp8 <name> <run a> <run b> <IDENTICAL|DIFFERENT|INFO>: l8_compare.py, its verdict judged
  "$PY" -I -B "$OUT_PY/tools/l8_compare.py" "$OUT_PY/L8/$2" "$OUT_PY/L8/$3" --json "$OUT_PY/L8/cmp/L8_$1.json" \
    > "$L8/compare_$1.txt" 2>&1
  local rc=$? got=ERROR
  # Judged on the verdict l8_compare.py prints AND its exit code together: a Python traceback also
  # exits 1, which alone would read as the DIFFERENT the two relative-step controls expect, so a
  # comparison that crashed would pass them without comparing anything (mistake 12; the review of
  # 31 October 2026, F2). Anything else, a JSON write failing after the verdict included, is ERROR,
  # and ERROR is never what a comparison expects, INFO included. The \r? takes a Windows line end.
  if [ $rc = 0 ] && grep -qxE $'VERDICT: IDENTICAL TRAINING\r?' "$L8/compare_$1.txt"; then
    got=IDENTICAL
  elif [ $rc = 1 ] && grep -qxE $'VERDICT: NOT IDENTICAL\r?' "$L8/compare_$1.txt"; then
    got=DIFFERENT
  fi
  echo "$1 $4 $got" >> "$L8/_verdicts.txt"
  echo "  $1: $(tail -n 1 "$L8/compare_$1.txt")   (expected: $4)"
}
: > "$L8/_verdicts.txt"
echo "comparisons:"
cmp8 extremes_sighted_seed0 ref_extremes/sighted_seed0 cand_extremes/sighted_seed0 IDENTICAL
cmp8 extremes_blind_seed0 ref_extremes/blind_seed0 cand_extremes/blind_seed0 IDENTICAL
cmp8 wideair_sighted_seed0 ref_wideair/sighted_seed0 cand_wideair/sighted_seed0 IDENTICAL
cmp8 ctl_none cand_extremes/sighted_seed0 ctl_none/sighted_seed0 IDENTICAL
cmp8 ctl_mass cand_extremes/sighted_seed0 ctl_mass/sighted_seed0 INFO
cmp8 ctl_cturb cand_extremes/sighted_seed0 ctl_cturb/sighted_seed0 INFO
cmp8 ctl_mass1e-9 cand_extremes/sighted_seed0 ctl_mass1e-9/sighted_seed0 DIFFERENT
cmp8 ctl_mass1e-6 cand_extremes/sighted_seed0 ctl_mass1e-6/sighted_seed0 DIFFERENT

# each run's identity, from its meta.json (run_l8_review.sh's block)
"$PY" - "$OUT_PY/L8" > "$L8/run_identities.txt" 2>&1 << 'EOF'
import glob, hashlib, json, os, sys
root = sys.argv[1]
out = {}
for meta in sorted(glob.glob(os.path.join(root, "*", "*", "meta.json"))):
    run = os.path.relpath(os.path.dirname(meta), root).replace(os.sep, "/")
    with open(meta, encoding="utf-8") as fh:
        m = json.load(fh)
    z = os.path.join(os.path.dirname(meta), "final.zip")
    zsha = None
    if os.path.exists(z):
        with open(z, "rb") as fh:
            zsha = hashlib.sha256(fh.read()).hexdigest()[:16]
    out[run] = dict(engine_sha=m.get("engine_sha"), plant_sha=m.get("plant_sha"), schema=m.get("schema"),
                    backend=m.get("backend"), train_road=m.get("train_road"), final_zip_sha256=zsha)
with open(os.path.join(root, "run_identities.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(out, indent=1))
EOF

BAD=$(awk '$3 == "ERROR" || (($2 == "IDENTICAL" || $2 == "DIFFERENT") && $2 != $3)' "$L8/_verdicts.txt" | wc -l)
for d in ref_extremes cand_extremes ref_wideair cand_wideair ctl_none ctl_mass ctl_cturb ctl_mass1e-9 ctl_mass1e-6; do
  rm -rf "${L8:?}/$d"
done
echo "run directories deleted (an identity test, not an experiment); kept: $L8"
if [ "$FAILED" = 0 ] && [ "$NRUNS" = 11 ] && [ "$BAD" = 0 ]; then
  echo "L8 VERDICT: PASS (11 runs exit 0; three pairs and the wrapper IDENTICAL; both relative-step controls DIFFERENT)"
  exit 0
fi
echo "L8 VERDICT: FAIL ($FAILED of $NRUNS runs did not exit 0; $BAD comparisons not as expected: $L8/_verdicts.txt)"
exit 1

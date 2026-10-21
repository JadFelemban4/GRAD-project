"""fetch_engine_data.py -- the public engine and vehicle data of decision 24, fetched and verified.

    python fetch_engine_data.py --verify-only        # download nothing: hash what the data folder holds
    python fetch_engine_data.py                      # download what is missing or wrong, then verify
    python fetch_engine_data.py --target D:\\engine-data --group epa-test-car-list --jobs 2

WHAT IT FETCHES
---------------
Every file in logs/epa/D3_AND_EPA_SOURCES.csv, each with its URL, size and sha256: the US EPA's
engine benchmarking packages for the Mazda 2.5 L turbo, the Honda 1.5 L L15B7 and the Ford 2.7 L
V6 (all fuels), EPA's Test Car Lists (the certification road loads in engine_specs/cars/), and
Argonne's Downloadable Dynamometer Database (D3) for the 2016 Mazda CX-9 and the 2018 Honda
Accord, about 2.4 GB. The list was written by `epa_map.py --stage` from the data folder's own
MANIFEST.csv of 20 October 2026; two Test Car Lists that folder never held are added there.

The default target is the team's data folder, C:\\Users\\badcl\\Desktop\\GRAD-engine-data. Its
layout is the list's `rel_path`, so a folder this script fills looks like that one.

WHAT IT WRITES
--------------
Only into the target folder, only the files listed, each first to "<name>.part" and renamed
into place only once its size and sha256 equal the list. A file already there with the right
hash is left alone; one with another hash is reported, and replaced only by a download that
verifies. It never writes into this repository: it refuses a target inside it. It reads two
files here, the source list and logs/epa/MANIFEST.csv.

It also checks the repository's own copies: every file in logs/epa/MANIFEST.csv must equal,
byte for byte, the member of the EPA package zip it was extracted from (zips present in the
target folder only). That closes the chain from EPA's URL to the file epa_map.py reads.

Exit code 0 when every listed file is present and verified and every member check passed;
1 otherwise. --verify-only never opens a network connection.

Argonne's D3 data may only be used with Argonne's attribution, which this script prints.

Added 20 October 2026, build step 1 of decision 24.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "logs", "epa", "D3_AND_EPA_SOURCES.csv")
REPO_MANIFEST = os.path.join(HERE, "logs", "epa", "MANIFEST.csv")
DEFAULT_TARGET = r"C:\Users\badcl\Desktop\GRAD-engine-data"

# Argonne's condition of use, verbatim from https://www.anl.gov/taps/downloadable-dynamometer-database
# (opened 20 October 2026; the data folder's CATALOGUE.md quotes the same sentence).
D3_ATTRIBUTION = ('"This data is from the Downloadable Dynamometer Database and was generated at the '
                  'Advanced Mobility Technology Laboratory (AMTL) at Argonne National Laboratory under the '
                  'funding and guidance of the U.S. Department of Energy (DOE)"')
USER_AGENT = "Mozilla/5.0 (GRAD-project fetch_engine_data.py; read-only research download)"
CHUNK = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def inside(path, root):
    """True when `path` is `root` or lies under it (both made absolute and case-folded)."""
    path, root = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return os.path.commonpath([path, root]) == root


def check(row, target):
    """('ok' | 'missing' | 'bad', detail) for one listed file."""
    p = os.path.join(target, row["rel_path"])
    if not os.path.exists(p):
        return "missing", ""
    size = os.path.getsize(p)
    if size != int(row["bytes"]):
        return "bad", f"{size:,} bytes, expected {int(row['bytes']):,}"
    got = sha256_file(p)
    return ("ok", "") if got == row["sha256"] else ("bad", f"sha256 {got[:16]}..., expected {row['sha256'][:16]}...")


def download(row, target, downloader, retries=3):
    """Fetch one file to <name>.part, verify size and sha256, rename into place. Returns a message."""
    dest = os.path.join(target, row["rel_path"])
    part = dest + ".part"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = ""
    for attempt in range(1, retries + 1):
        try:
            if downloader == "curl":
                subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error", "-A", USER_AGENT,
                                "-o", part, row["url"]], check=True, timeout=3600)
            else:
                req = urllib.request.Request(row["url"], headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=120) as r, open(part, "wb") as fh:
                    shutil.copyfileobj(r, fh, CHUNK)
            size, got = os.path.getsize(part), sha256_file(part)
            if size == int(row["bytes"]) and got == row["sha256"]:
                os.replace(part, dest)
                return f"fetched  {row['rel_path']} ({size:,} bytes)"
            last = f"downloaded {size:,} bytes with sha256 {got[:16]}..., expected {row['sha256'][:16]}..."
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            last = f"{type(e).__name__}: {e}"
        if os.path.exists(part):
            os.remove(part)
        time.sleep(2 * attempt)
    return f"FAILED   {row['rel_path']}: {last}"


def member_checks(target, sources):
    """Each repository copy in logs/epa/MANIFEST.csv against the member of its package zip."""
    zips = {s["url"]: os.path.join(target, s["rel_path"]) for s in sources}
    results = []
    for r in read_csv(REPO_MANIFEST):
        z = zips.get(r["url"])
        if z is None or not os.path.exists(z):
            results.append(("missing", r["repo_path"], "its package zip is not in the target folder"))
            continue
        with zipfile.ZipFile(z) as zf:
            data = zf.read(r["zip_member"])
        member = hashlib.sha256(data).hexdigest()
        copy = sha256_file(os.path.join(HERE, r["repo_path"]))
        if member == r["sha256"] == copy:
            results.append(("ok", r["repo_path"], ""))
        else:
            results.append(("bad", r["repo_path"], f"member {member[:16]}..., repo copy {copy[:16]}..., "
                                                   f"manifest {r['sha256'][:16]}..."))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--target", default=DEFAULT_TARGET, help=f"data folder (default {DEFAULT_TARGET})")
    ap.add_argument("--verify-only", action="store_true", help="download nothing; hash what is there")
    ap.add_argument("--group", action="append", help="only this group of the list (repeatable)")
    ap.add_argument("--jobs", type=int, default=4, help="parallel downloads and hashes (default 4)")
    ap.add_argument("--downloader", choices=("urllib", "curl"), default="urllib",
                    help="urllib (default) or the curl program, if epa.gov refuses Python's TLS")
    ap.add_argument("--sources", default=SOURCES, help="another list in the same form (for testing this script)")
    a = ap.parse_args()

    print(f"Argonne D3 data may only be used with this attribution:\n  {D3_ATTRIBUTION}\n")
    target = os.path.abspath(a.target)
    if inside(target, HERE):
        sys.exit(f"REFUSED: {target} is inside the repository. This script never writes there.")
    sources = read_csv(a.sources)
    rows = [s for s in sources if not a.group or s["group"] in a.group]
    for s in rows:
        if not inside(os.path.join(target, s["rel_path"]), target):
            sys.exit(f"REFUSED: {s['rel_path']} would land outside {target}")
    mode = "verify only, no network" if a.verify_only else f"download what is missing ({a.downloader})"
    shown = os.path.relpath(a.sources, HERE) if inside(a.sources, HERE) else a.sources
    print(f"target {target}\nlist   {shown}: {len(rows)} files, "
          f"{sum(int(s['bytes']) for s in rows):,} bytes; {mode}")
    if not a.verify_only:
        os.makedirs(target, exist_ok=True)
    elif not os.path.isdir(target):
        sys.exit(f"no folder at {target}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        state = dict(zip((s["rel_path"] for s in rows), pool.map(lambda s: check(s, target), rows)))
        if not a.verify_only:
            todo = [s for s in rows if state[s["rel_path"]][0] != "ok"]
            for msg in pool.map(lambda s: download(s, target, a.downloader), todo):
                print("  " + msg)
            for s in todo:
                state[s["rel_path"]] = check(s, target)

    print("\nby group (ok / missing / wrong bytes):")
    for g in sorted({s["group"] for s in rows}):
        mine = [s for s in rows if s["group"] == g]
        n = {k: sum(1 for s in mine if state[s["rel_path"]][0] == k) for k in ("ok", "missing", "bad")}
        print(f"  {g:<30} {n['ok']:>4} / {n['missing']:>3} / {n['bad']:>3}   of {len(mine)}")
    for s in rows:
        st, detail = state[s["rel_path"]]
        if st != "ok":
            print(f"  {st.upper():<8} {s['rel_path']}" + (f": {detail}" if detail else "")
                  + (f"  [{s['note']}]" if s["note"] else ""))
    n_ok = sum(1 for s in rows if state[s["rel_path"]][0] == "ok")

    members = member_checks(target, sources)
    m_ok = sum(1 for m in members if m[0] == "ok")
    print(f"\nlogs/epa/ against the package zips: {m_ok} of {len(members)} files equal their zip member")
    for st, path, detail in members:
        if st != "ok":
            print(f"  {st.upper():<8} {path}: {detail}")

    good = n_ok == len(rows) and m_ok == len(members)
    print(f"\n{'ALL VERIFIED' if good else 'NOT ALL VERIFIED'}: {n_ok} of {len(rows)} listed files, "
          f"{m_ok} of {len(members)} repository copies.")
    print(f"Argonne D3 attribution (required wherever D3 data are used):\n  {D3_ATTRIBUTION}")
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()

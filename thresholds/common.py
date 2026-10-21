"""common.py -- the paths, hashes and file writers every step of engine_thresholds.py uses."""
import contextlib
import hashlib
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(REPO, "data", "engines")          # epa_map.py's tables (generated, -text)
OUT_DIR = os.path.join(REPO, "results", "ENGINE_THRESHOLDS")  # every step's output and printout
ECU_DIR = os.path.join(OUT_DIR, "ecu")                         # step 5, one file per run
CONTRACT_JSON = os.path.join(REPO, "results", "ENGINE_THRESHOLDS.json")
CONTRACT_MD = os.path.join(REPO, "results", "ENGINE_THRESHOLDS.md")
TEMPLATE_MD = os.path.join(REPO, "thresholds", "document_template.md")
# The team's data folder, outside the repository (fetch_engine_data.py's target; test_epa_map.py
# reads the same variable). Step 6 hashes the D3 files C3 may read and checks them against it.
DATA_FOLDER = os.environ.get("GRAD_ENGINE_DATA", r"C:\Users\badcl\Desktop\GRAD-engine-data")
EPA_ENGINES = ("mazda_25t", "honda_l15b7", "ford_27tt")


def rel(path):
    """A path as the documents name it: repository-relative, forward slashes."""
    return os.path.relpath(path, REPO).replace("\\", "/")


def sha_raw(path):
    """sha256 of a file's bytes. For files stored and checked out byte for byte: the EPA tables
    (data/engines/.gitattributes) and the D3 files, which the data folder's MANIFEST.csv pins."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_text(path):
    """sha256 of a text file with every CRLF read as LF. This repository is core.autocrlf=true,
    so one commit checks out as CRLF on Windows and LF elsewhere (fingerprint._sha_files says
    why that is load-bearing); the generators and the step outputs are hashed this way, so a
    teammate's clone gives the hashes the JSON records."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj, ascii_only=True):
    """json.dump with indent 1, as the scratch generators of 21 October wrote their outputs, but
    always with LF line endings."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=ascii_only)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class _Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


@contextlib.contextmanager
def printout(name, write=True):
    """Everything a step prints goes to the console AND to results/ENGINE_THRESHOLDS/<name>.txt,
    so each step's printed output is kept beside its numbers."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(_Tee(sys.stdout, buf)):
        yield
    if write:
        write_text(os.path.join(OUT_DIR, f"{name}.txt"), buf.getvalue())

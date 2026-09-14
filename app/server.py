"""server.py — the local host. Streams live engine state to anything that connects.

    python -m app.server --replay logs/raw/7475b5d7-20260908_142743.csv
    python -m app.server --replay logs/raw/pull01-20260913_093527.csv --speed 8
    python -m app.server --live

Then open http://localhost:8000

    /          the full dashboard, for a stationary reader
    /driver    DRIVER MODE. one number, one colour, audio. safe to glance at.
    /review    what was marked on past drives, for a mechanic or an owner.

WHAT THIS IS
------------
A local mirror of the engine's state, including the parts the car has no gauge
for. It reads the OBD-II port, runs the validated physics alongside it, and
pushes the result to any browser on the machine over a websocket.

RAW DATA IS NOT STORED. The stream is in memory and gone. Only alerts -- what
the model marks as irregular -- are written, to app/review_log.jsonl, for a
workshop or owner to read afterwards. That separation is deliberate and it is
the product's privacy model. See reader.py.

READ-ONLY, PERMANENTLY
----------------------
This app never transmits to the vehicle. It opens the OBD-II port for reading
and issues no write commands, no mode 08, nothing. Advice is rendered to a
human on a screen; a human decides what to do with it.

If a future version is ever asked to suggest ECU parameters, the SUGGESTION is
text on a screen and stays here. APPLYING it is a different product with
different safety obligations, and this codebase is not the place for it. The
separation is structural: there is no code path from this process to the bus.
Every HTTP route below is a GET.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import threading
import time
from queue import Queue, Empty, Full

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect      # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse         # noqa: E402

from app.estimator import Estimator, SEED_SETTLED_K              # noqa: E402
from app.alerts import (AlertEngine, TURB_PROTECT_K, OIL_PROTECT_K,  # noqa: E402
                        VALID_MAP_LO, VALID_MAP_HI, MISMATCH_PCT)
from app.reader import ReplayReader, LiveReader, Stream          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Served to the browser so no page carries its own copy of a threshold.
# generality_test.py and check_premise.py already share TURB_PROTECT_K for
# exactly this reason -- two places reporting different protection limits is a
# bug that looks like a disagreement. The UI is a third place.
LIMITS = {
    "turb_c": round(TURB_PROTECT_K - 273.15, 1),
    "oil_c": round(OIL_PROTECT_K - 273.15, 1),
    "seed_settled_k": SEED_SETTLED_K,
    "valid_map_kpa": [VALID_MAP_LO, VALID_MAP_HI],
    "mismatch_pct": MISMATCH_PCT,
}
app = FastAPI(title="Engine Supervisor — live")
# Set here as well as in main() so that /api/review still works if this module
# is served by an external ASGI runner that never calls main().
app.state.review_path = os.path.join(HERE, "review_log.jsonl")

_latest: dict = {"state": {"ok": False}, "alerts": [], "meta": {}}
_alerts: list = []
_meta = {"source": "not started", "mode": "-", "reader": {}, "error": None,
         "limits": LIMITS}

# One queue per connected browser. A single shared queue would have each socket
# CONSUMING the payloads the others need -- two tabs open and each sees roughly
# half the stream. Subscribers are added and removed under a lock because the
# reader thread publishes while the event loop iterates.
_subs: list[Queue] = []
_subs_lock = threading.Lock()


def _publish(payload: dict):
    _latest.clear()
    _latest.update(payload)
    with _subs_lock:
        targets = list(_subs)
    for q in targets:
        try:
            q.put_nowait(payload)
        except Full:
            # A browser that cannot keep up loses frames. It must never stall
            # the reader, because the reader is holding a real-time stream.
            try:
                q.get_nowait()
                q.put_nowait(payload)
            except (Empty, Full):
                pass


def _pump(reader, estimator, alerts):
    """Runs in a background thread: read -> estimate -> detect -> publish."""
    stream = Stream(reader)
    try:
        for s in stream:
            st = estimator.update(s)
            new = alerts.check(st, s) if st.ok else []
            status = stream.status
            _meta["reader"] = status.as_dict() if status else {}
            payload = {"state": st.as_dict(),
                       "alerts": [a.__dict__ for a in new],
                       "meta": dict(_meta)}
            for a in new:
                _alerts.append(a.__dict__)
            _publish(payload)
    except Exception as e:
        # A dead reader thread that says nothing is the worst failure mode
        # here: the UI would keep showing the last state as though it were
        # live. Say so instead, in the payload the browser is already reading.
        _meta["error"] = f"{type(e).__name__}: {e}"
        _meta["mode"] = "stopped"
        _publish({"state": {"ok": False}, "alerts": [], "meta": dict(_meta)})
        return
    _meta["mode"] = "finished"
    _publish({"state": _latest.get("state", {"ok": False}),
              "alerts": [], "meta": dict(_meta)})


def _page(name: str) -> str:
    with open(os.path.join(HERE, "static", name), encoding="utf-8") as fh:
        return fh.read()


@app.get("/", response_class=HTMLResponse)
def index():
    return _page("index.html")


@app.get("/driver", response_class=HTMLResponse)
def driver():
    """Driver mode. One number, one colour, audio for thermal alerts only."""
    return _page("driver.html")


@app.get("/review", response_class=HTMLResponse)
def review():
    """What was marked, for a mechanic or an owner reading after the drive."""
    return _page("review.html")


@app.get("/api/state")
def state():
    """Current state, for anything that would rather poll than hold a socket."""
    return JSONResponse(_latest)


@app.get("/api/alerts")
def alerts_so_far():
    """Everything marked this session. The same records go to the review file."""
    return JSONResponse({"session_alerts": _alerts, "count": len(_alerts)})


@app.get("/api/status")
def status():
    """Link health: which channels are answering, and which have been retired."""
    return JSONResponse(_meta)


@app.get("/api/review")
def review_data():
    """The marked events from every past session, newest session first.

    Reads app/review_log.jsonl -- the ONLY file this product writes. A record
    that will not parse is skipped and counted rather than failing the page;
    the file is append-only and a half-written last line is normal after a
    power cut.
    """
    path = app.state.review_path
    sessions: dict[str, dict] = {}
    bad = 0
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                sid = rec.get("session", "unknown")
                s = sessions.setdefault(sid, {
                    "session": sid, "source": rec.get("source", "unknown"),
                    "first_wall": rec.get("wall"), "last_wall": rec.get("wall"),
                    "events": [], "counts": {}})
                s["events"].append(rec)
                s["last_wall"] = rec.get("wall") or s["last_wall"]
                k = rec.get("kind", "?")
                s["counts"][k] = s["counts"].get(k, 0) + 1
    except FileNotFoundError:
        return JSONResponse({"sessions": [], "unreadable_lines": 0,
                             "note": "nothing has been marked yet"})
    out = sorted(sessions.values(), key=lambda s: s["first_wall"] or "",
                 reverse=True)
    for s in out:
        s["events"].sort(key=lambda r: r.get("t", 0.0))
    return JSONResponse({"sessions": out, "unreadable_lines": bad})


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    q: Queue = Queue(maxsize=200)
    with _subs_lock:
        _subs.append(q)
    try:
        # Whatever we have right now, so a browser that connects mid-drive is
        # not blank until the next sample.
        await sock.send_text(json.dumps(_latest))
        while True:
            try:
                payload = q.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
                continue
            await sock.send_text(json.dumps(payload))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        with _subs_lock:
            if q in _subs:
                _subs.remove(q)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--replay", metavar="CSV", help="replay one of our logs")
    g.add_argument("--live", action="store_true", help="read the car")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="replay speed multiplier (0 = as fast as possible)")
    ap.add_argument("--loop", action="store_true",
                    help="restart the replay when it reaches the end")
    ap.add_argument("--port", default=None, help="serial port for the adapter")
    ap.add_argument("--http-port", type=int, default=8000)
    ap.add_argument("--review", default=os.path.join(HERE, "review_log.jsonl"))
    a = ap.parse_args()

    if a.replay:
        reader = ReplayReader(a.replay, speed=a.speed, loop=a.loop)
        _meta.update(source=reader.name,
                     mode=f"replay x{a.speed if a.speed else 'max'}")
        missing = sorted({c for c in ("rpm", "air_kgh", "ect_c", "t_amb_c",
                                      "v_kmh", "boost_psi")
                          if c not in reader.present})
        if missing:
            print(f"  note       this log does not carry: {', '.join(missing)}")
            print(f"             the estimator will model them and say so")
    else:
        reader = LiveReader(port=a.port)
        _meta.update(source="live OBD-II", mode="live")

    app.state.review_path = a.review
    est = Estimator()
    al = AlertEngine(review_path=a.review, source=_meta["source"])
    threading.Thread(target=_pump, args=(reader, est, al), daemon=True).start()

    print(f"  source     {_meta['source']}  ({_meta['mode']})")
    print(f"  raw data   IN MEMORY ONLY, never written")
    print(f"  marked     {a.review}")
    print(f"  open       http://localhost:{a.http_port}          full dashboard")
    print(f"             http://localhost:{a.http_port}/driver   driver mode")
    print(f"             http://localhost:{a.http_port}/review   past drives\n")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=a.http_port, log_level="warning")


if __name__ == "__main__":
    main()

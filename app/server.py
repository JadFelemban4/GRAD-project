"""server.py — the local host. Streams live engine state to anything that connects.

    python -m app.server --replay logs/raw/7475b5d7-20260908_142743.csv
    python -m app.server --replay logs/raw/pull01-20260913_093527.csv --speed 8
    python -m app.server --live

Then open http://localhost:8000

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
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import threading
from queue import Queue, Empty

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect      # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse         # noqa: E402

from app.estimator import Estimator                              # noqa: E402
from app.alerts import AlertEngine                               # noqa: E402
from app.reader import ReplayReader, LiveReader, Stream          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="Engine Supervisor — live")

_q: Queue = Queue(maxsize=200)
_latest = {"ok": False}
_alerts: list = []
_meta = {"source": "not started", "mode": "-"}


def _pump(reader, estimator, alerts):
    """Runs in a background thread: read -> estimate -> detect -> queue."""
    for s in Stream(reader):
        st = estimator.update(s)
        new = alerts.check(st, s) if st.ok else []
        payload = {"state": st.as_dict(),
                   "alerts": [a.__dict__ for a in new],
                   "meta": _meta}
        _latest.clear()
        _latest.update(payload)
        for a in new:
            _alerts.append(a.__dict__)
        try:
            _q.put_nowait(payload)
        except Exception:
            pass          # a slow browser must never stall the reader
    _meta["mode"] = "finished"


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(HERE, "static", "index.html"), encoding="utf-8") as fh:
        return fh.read()


@app.get("/api/state")
def state():
    """Current state, for anything that would rather poll than hold a socket."""
    return JSONResponse(_latest)


@app.get("/api/alerts")
def alerts_so_far():
    """Everything marked this session. The same records go to the review file."""
    return JSONResponse({"session_alerts": _alerts, "count": len(_alerts)})


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    try:
        while True:
            try:
                payload = _q.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
                continue
            await sock.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--replay", metavar="CSV", help="replay one of our logs")
    g.add_argument("--live", action="store_true", help="read the car")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="replay speed multiplier (0 = as fast as possible)")
    ap.add_argument("--port", default=None, help="serial port for the adapter")
    ap.add_argument("--review", default=os.path.join(HERE, "review_log.jsonl"))
    a = ap.parse_args()

    if a.replay:
        reader = ReplayReader(a.replay, speed=a.speed)
        _meta.update(source=reader.name, mode=f"replay x{a.speed or 'max'}")
    else:
        reader = LiveReader(port=a.port)
        _meta.update(source="live OBD-II", mode="live")

    est = Estimator()
    al = AlertEngine(review_path=a.review, source=_meta["source"])
    threading.Thread(target=_pump, args=(reader, est, al), daemon=True).start()

    print(f"  source     {_meta['source']}  ({_meta['mode']})")
    print(f"  raw data   IN MEMORY ONLY, never written")
    print(f"  marked     {a.review}")
    print(f"  open       http://localhost:8000\n")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()

"""Laya behind one JSON line per request. Runs ONLY under Laya's own python:

    <LAYA_HOME>/.venv/Scripts/python.exe -I -B -X utf8 laya_worker.py <absolute model_dir>

app/laya_bridge.py starts it with cwd=LAYA_HOME. The server never imports it:
the server's interpreter has no laya, transformers or safetensors (design M3
section 7.5). -I keeps app/ off sys.path, so nothing from the repository can
be imported here, and -B writes no bytecode anywhere.

The protocol is the REAL stdout, one JSON line at a time: one ready line, then
one reply per request line read from stdin. sys.stdout is pointed at stderr
before laya is imported, because laya prints its warnings to stdout. A failure
is reported by its exception CLASS name, never by its text. The worker stays
alive after a bad request and exits at stdin EOF.

THE NETWORK GUARD COMES FIRST, before torch or laya exist. Every entry point
in GUARDED that this platform has is replaced by _refuse, which counts the
attempt and raises OSError. Each reply carries the running count, and the
bridge kills a worker whose count is not zero. An entry point the platform
does not have is left absent: socket.socket has no sendmsg on Windows, and
adding one sends asyncio down its Unix branch (os.sysconf), so `import torch`
failed (measured 28 September). The count sees Python's socket API only: a
native library that opens its own connection is not seen by it. Nor is
asyncio's proactor on Windows, which connects through the overlapped
module's ConnectEx, so a connection an event loop makes to a numeric address
calls no guarded entry point (measured 29 September on a loop built before
the guard: refused by the OS, attempts 0). In this worker no loop can exist
to do that: on Windows a loop's self-pipe is a loopback socketpair, which the
guard refuses and counts, so no event loop can be built after it.
"""
import socket

_NET = {"attempts": 0}


def _refuse(*args, **kwargs):
    """Count one network attempt and refuse it."""
    _NET["attempts"] += 1
    raise OSError("the Laya worker makes no network calls")


GUARDED = (("socket", "connect"), ("socket", "connect_ex"), ("socket", "sendto"),
           ("socket", "sendmsg"), ("module", "create_connection"),
           ("module", "getaddrinfo"), ("module", "gethostbyname"),
           ("module", "gethostbyname_ex"))
for _where, _name in GUARDED:
    _owner = socket.socket if _where == "socket" else socket
    if hasattr(_owner, _name):
        setattr(_owner, _name, _refuse)

import json  # noqa: E402  (after the guard, on purpose)
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

WARM_UP = {"warm_up": {"type": "choice", "instructions": "Is this a warm-up call?",
                       "criteria": {"yes": "a warm-up call", "no": "a real question"}}}


def main():
    """Load Laya once, send the ready line, then answer stdin line by line."""
    proto = sys.stdout
    sys.stdout = sys.stderr

    def send(obj):
        print(json.dumps(obj), file=proto, flush=True)

    model_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    if not (os.path.isabs(model_dir) and os.path.isdir(model_dir)):
        send({"ready": False, "error": "NotADirectoryError"})
        return 1
    t0 = time.perf_counter()
    try:
        from importlib.metadata import version
        import torch
        import laya
        agent = laya.load(model_dir, device="cuda" if torch.cuda.is_available() else "cpu")
        agent.predict({"warm_up": True}, WARM_UP)
        ready = {"ready": True, "device": str(agent.device), "laya": version("laya"),
                 "load_s": round(time.perf_counter() - t0, 2)}
    except Exception as exc:
        send({"ready": False, "error": type(exc).__name__})
        return 1
    send(ready)
    for line in sys.stdin:
        if not line.strip():
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            t = time.perf_counter()
            out = agent.predict(req["state"], req["questions"])
            reply = {"id": rid, "ok": True, "device": str(agent.device),
                     "ms": round((time.perf_counter() - t) * 1000.0, 1),
                     "model": out.get("model"), "answers": out.get("answers"),
                     "usage": out.get("usage"), "net_attempts": _NET["attempts"]}
            json.dumps(reply)
        except Exception as exc:
            reply = {"id": rid, "ok": False, "error": type(exc).__name__,
                     "net_attempts": _NET["attempts"]}
        send(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())

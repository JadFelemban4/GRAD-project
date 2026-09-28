"""Laya's worker, seen from the server: find it, start it, ask it, stop it.

Laya runs in its OWN interpreter (LAYA_HOME/.venv), because the server's has
no laya, transformers or safetensors, and installing them would change the
interpreter that runs the scored == proof (design M3 section 7.5). So the
bridge starts app/laya_worker.py under Laya's python and speaks JSON lines to
it: one request per line on the worker's stdin, one reply per line back.

WHEN A WORKER EXISTS. Building a LayaBridge reads no file and starts nothing,
and status() never starts one either. Only ask(), which only a press of
«اسأل لايا» reaches, starts the worker, and only when none is alive. It then
stays resident until the server stops: close() is registered with atexit on
the first start, and closes stdin, waits CLOSE_WAIT_S, then kills.

EVERY PRESS ASKS TWICE (design 7.5b): QUESTIONS, the very object jev gets,
then QUESTIONS_REVERSED, the same questions with each one's five options in
reverse order. Laya is deterministic, so a choice that differs between the two
changed with the order alone.

WHAT KILLS THE WORKER: no ready line within start_timeout, no answer within
answer_timeout, a reply whose id is not the request's, and a reply whose
network count is not zero. A late line would put the protocol out of step, so
the next press starts a fresh worker. A reply of ok: false (worker_error) and
an answer to_action refuses (bad_answer) leave it running.

THE WORKER'S ENVIRONMENT is the server's without TYPESAFE_API_KEY or any
HF_TOKEN*, with Hugging Face forced offline. Its stderr goes to the server's
console, never to a file. The only print that does not go to stderr is the
request line into the worker's stdin: a pipe to a process on this machine,
not a path to the vehicle.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from app.model_questions import (QUESTIONS, QUESTIONS_REVERSED, REPO, build_state, to_action,
                                 user_setting)

WORKER = Path(__file__).resolve().parent / "laya_worker.py"
START_TIMEOUT_S = 90.0
ANSWER_TIMEOUT_S = 20.0
CLOSE_WAIT_S = 5.0
KINDS = ("ValueError", "RuntimeError", "OutOfMemoryError")
OFFLINE = {"USE_TF": "0", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
           "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"}


class LayaError(Exception):
    """A fixed code (design 7.9) and, for worker_error only, a fixed kind."""

    def __init__(self, code, kind=None):
        super().__init__(code)
        self.code, self.kind = code, kind


def _under_repo(path):
    p = Path(path).resolve()
    return p == REPO or REPO in p.parents


def load_home():
    """(python, model_dir, source) for LAYA_HOME, or LayaError.

    The one place a setting's VALUE is checked as a path: the folder must be
    absolute, and neither it, its python nor its model may resolve under the
    repository. not_configured: no LAYA_HOME at all; not_found: anything else.
    """
    value, source = user_setting("LAYA_HOME", "laya_home")
    if not value:
        raise LayaError("not_configured")
    home = Path(value)
    python = home / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    model_dir = home / "models" / "multilingual"
    if (not home.is_absolute() or _under_repo(home) or _under_repo(python)
            or _under_repo(model_dir) or not python.is_file()
            or not (model_dir / "rl_agent_config.json").is_file()):
        raise LayaError("not_found")
    return str(python), str(model_dir.resolve()), source


def worker_env(home=None):
    """The server's environment without the jev key or any HF token, offline."""
    env = {k: v for k, v in os.environ.items()
           if k.upper() != "TYPESAFE_API_KEY" and not k.upper().startswith("HF_TOKEN")}
    env.update(OFFLINE)
    if home is not None:
        env["HF_HOME"] = str(Path(home) / ".cache" / "huggingface")
    return env


def _pump(stream, lines):
    """The reader thread: every stdout line onto the queue, then None at EOF.
    A pipe cannot be read with a timeout on Windows; a queue can."""
    try:
        for line in stream:
            lines.put(line)
    except (OSError, ValueError):
        pass
    finally:
        lines.put(None)
        try:
            stream.close()
        except OSError:
            pass


class LayaBridge:
    """One Laya worker, started by the first ask and kept until close().

    `command` replaces the real spawn (tests pass a fake worker run by
    sys.executable); it is then started with no cwd and worker_env(None).
    `spawns` counts Popen calls; `ready` is a live worker's ready line.
    """

    def __init__(self, command=None, start_timeout=START_TIMEOUT_S,
                 answer_timeout=ANSWER_TIMEOUT_S):
        self._command = list(command) if command is not None else None
        self.start_timeout, self.answer_timeout = start_timeout, answer_timeout
        self._proc = None
        self._lines = None
        self._next_id = 0
        self._starting = False
        self._failed = None
        self._atexit = False
        self.ready = None
        self.spawns = 0

    def _alive(self):
        # One read: status() runs on the status route's thread, beside an ask
        # whose kill can set _proc to None between two reads.
        proc = self._proc
        return proc is not None and proc.poll() is None

    def status(self):
        """What the page's Laya column shows. Reads the setting; never spawns."""
        if self._command is not None:
            configured, source, problem = True, "command", None
        else:
            _value, source = user_setting("LAYA_HOME", "laya_home")
            try:
                load_home()
                configured, problem = True, None
            except LayaError as err:
                configured, problem = err.code != "not_configured", err.code
        alive = self._alive()
        worker = ("starting" if self._starting else "ready" if alive
                  else "failed" if self._failed else "stopped")
        if problem is None and worker == "failed":
            problem = self._failed
        ready = self.ready if alive else None
        return {"configured": configured, "source": source, "problem": problem,
                "worker": worker, "device": ready.get("device") if ready else None,
                "laya": ready.get("laya") if ready else None}

    def _kill(self):
        """Kill and reap the worker, and forget it: the next ask starts another."""
        proc, self._proc, self._lines, self.ready = self._proc, None, None, None
        if proc is None:
            return
        try:
            proc.kill()
            proc.wait(CLOSE_WAIT_S)
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            proc.stdin.close()
        except OSError:
            pass

    def _start(self):
        """Spawn, wait for the ready line, and return the seconds it took."""
        if self._command is not None:
            cmd, home = self._command, None
        else:
            python, model_dir, _source = load_home()
            home = str(Path(model_dir).parents[1])
            cmd = [python, "-I", "-B", "-X", "utf8", str(WORKER), model_dir]
        self._starting = True
        try:
            self.spawns += 1
            t0 = time.perf_counter()
            try:
                proc = subprocess.Popen(cmd, cwd=home, env=worker_env(home),
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=None, text=True, encoding="utf-8")
            except OSError:
                self._failed = "start_failed"
                raise LayaError("start_failed") from None
            lines = queue.Queue()
            threading.Thread(target=_pump, args=(proc.stdout, lines), daemon=True,
                             name="laya-reader").start()
            if not self._atexit:
                atexit.register(self.close)
                self._atexit = True
            self._proc = proc
            try:
                line = lines.get(timeout=self.start_timeout)
            except queue.Empty:
                self._kill()
                self._failed = "start_timeout"
                raise LayaError("start_timeout") from None
            try:
                ready = json.loads(line) if line is not None else None
            except ValueError:
                ready = None
            if not isinstance(ready, dict) or ready.get("ready") is not True:
                self._kill()
                self._failed = "start_failed"
                raise LayaError("start_failed")
            self._lines, self.ready, self._failed = lines, ready, None
            return round(time.perf_counter() - t0, 2)
        finally:
            self._starting = False

    def _request(self, state, questions):
        """One request line out, one reply line back, checked; the reply dict."""
        self._next_id += 1
        rid = self._next_id
        proc = self._proc
        try:
            print(json.dumps({"id": rid, "state": state, "questions": questions}),
                  file=proc.stdin, flush=True)
        except (OSError, ValueError):
            self._kill()
            raise LayaError("worker_died") from None
        try:
            raw = self._lines.get(timeout=self.answer_timeout)
        except queue.Empty:
            self._kill()
            raise LayaError("timeout") from None
        if raw is None:
            self._kill()
            raise LayaError("worker_died")
        try:
            reply = json.loads(raw)
        except (ValueError, RecursionError):      # deep nesting exhausts json.loads
            reply = None
        if not isinstance(reply, dict) or reply.get("id") != rid:
            self._kill()
            raise LayaError("bad_answer")
        if reply.get("net_attempts") != 0:
            self._kill()
            raise LayaError("network_attempt")
        if reply.get("ok") is not True:
            kind = reply.get("error")
            raise LayaError("worker_error", kind if kind in KINDS else "other")
        return reply

    def ask(self, trace, step):
        """Ask Laya about one second, twice: the design's order, then reversed."""
        state = build_state(trace, step)
        started_s = None
        if not self._alive():
            self._kill()             # none yet, or one that died since the last press
            started_s = self._start()
        t0 = time.perf_counter()
        forward = self._request(state, QUESTIONS)
        reverse = self._request(state, QUESTIONS_REVERSED)
        ms = round((time.perf_counter() - t0) * 1000.0, 1)
        try:
            answers = to_action(forward.get("answers"))
            answers_reversed = to_action(reverse.get("answers"))
        # BadAnswer is a ValueError; a huge integer overflows in to_action.
        except (ValueError, OverflowError):
            raise LayaError("bad_answer") from None
        name = forward.get("model")
        return {"model_name": name if isinstance(name, str) and len(name) <= 64 else None,
                "laya": (self.ready or {}).get("laya"), "device": forward.get("device"),
                "ms": ms, "started_s": started_s,
                "answers": answers, "answers_reversed": answers_reversed,
                "usage": [forward.get("usage"), reverse.get("usage")],
                "sent": [{"state": state, "questions": QUESTIONS},
                         {"state": state, "questions": QUESTIONS_REVERSED}]}

    def close(self):
        """Close stdin, wait CLOSE_WAIT_S for the worker to exit, then kill. Idempotent."""
        proc, self._proc, self._lines, self.ready = self._proc, None, None, None
        if proc is None:
            return
        try:
            proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(CLOSE_WAIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(CLOSE_WAIT_S)

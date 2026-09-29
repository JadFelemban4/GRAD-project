"""jev, the external language model (typesafe.ai), asked about one simulated
second (agent replay M3, design section 7.4).

One press is one paid call: a POST to URL with model MODEL, the state and the
five questions from app.model_questions, a TIMEOUT_S timeout, no retry and no
redirect followed.
The answer is shown, never applied, averaged, compared with the agents or
saved.

The key is read on every call. A key pasted on the page (29 Sep, after M3)
wins: the server holds it in a SessionKey, in this process's memory only, and
passes it to ask(). Otherwise it comes from TYPESAFE_API_KEY or from
<APPDATA>/grad-project/typesafe_key (model_questions.user_setting). It
appears in one place only: the Authorization header that _send builds. It is
never logged, returned, written to a file or put into an error. Every failure
is a JevError with a fixed code; vendor_status also keeps the integer HTTP
status. Neither str(exc) nor the vendor's body is ever kept.

Imported only by app.agent_api.install(), which only the --simulation branch
of app/server.py calls. Nothing here has a path to the vehicle.
"""
from __future__ import annotations

import http.client
import json
import threading
import time
import urllib.error
import urllib.request

from app.model_questions import QUESTIONS, build_state, to_action, user_setting

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
TIMEOUT_S = 10.0
# The statuses the vendor documents. Any other non-2xx reply is vendor_status
# (design C14): an account with no credit gets a status nobody has documented.
STATUS_CODES = {401: "key_rejected", 403: "vendor_refused", 422: "request_rejected",
                429: "rate_limited", 529: "overloaded"}


class JevError(Exception):
    """A fixed code; `status` is the integer HTTP status for vendor_status only."""

    def __init__(self, code, status=None):
        super().__init__(code)
        self.code = code
        self.status = status


def _header_safe(key):
    """True when 'Bearer <key>' can go into an HTTP header: every character
    latin-1, none of them a control or other unprintable character."""
    return key.isprintable() and all(ord(c) < 256 for c in key)


def load_key():
    """(key, 'env' | 'file'), or (None, None). Read on each call, never kept.

    A key no HTTP header can carry counts as no key, so ask() raises no_key
    and sends nothing. Measured 29 Sep, offline: for a character outside
    latin-1 (a pasted curly quote) http.client raises a UnicodeEncodeError
    whose repr holds the whole header, key included, and for a line break a
    ValueError whose text holds it. user_setting already refuses an
    unprintable key FILE the same way.
    """
    key, source = user_setting("TYPESAFE_API_KEY", "typesafe_key")
    if key is None or not _header_safe(key):
        return None, None
    return key, source


class SessionKey:
    """The jev key pasted on the page (Jad, 29 Sep, after M3): held in this
    process's memory only, gone when the server stops, never written to a file.

    set() strips surrounding whitespace and keeps the value only if an HTTP
    header can carry it (_header_safe) and it is MIN_LEN to MAX_LEN characters
    long; otherwise it keeps nothing new and returns False, so a refused value
    leaves the key already held. repr and str say only whether a key is held,
    and __slots__ leaves no __dict__ for vars() to show.
    """

    MIN_LEN, MAX_LEN = 8, 512
    __slots__ = ("_lock", "_value")

    def __init__(self):
        self._lock = threading.Lock()
        self._value = None

    def set(self, value):
        if not isinstance(value, str):
            return False
        value = value.strip()
        if not (self.MIN_LEN <= len(value) <= self.MAX_LEN and _header_safe(value)):
            return False
        with self._lock:
            self._value = value
        return True

    def clear(self):
        with self._lock:
            self._value = None

    def get(self):
        with self._lock:
            return self._value

    def __repr__(self):
        return f"SessionKey({'empty' if self.get() is None else 'set'})"

    __str__ = __repr__


def build_request(trace, step):
    """The exact body sent, which the page shows as 'what was sent': no key in it."""
    return {"model": MODEL, "state": build_state(trace, step), "questions": QUESTIONS}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Every redirect is refused, so it reaches ask() as its status.

    Measured 29 Sep, offline: urllib's default opener answers a 301, 302 or 303
    to this POST with a GET to the Location, http:// included, and carries the
    Authorization header along: the key sent to another host, and two requests
    for one press. Returning None here hands the reply to urllib's default error
    handler, which raises HTTPError(code). Refusing before the Location is read
    also means a Location urllib cannot parse raises no ValueError out of _send,
    as it would if redirect_request refused instead.
    """

    def http_error_302(self, req, fp, code, msg, headers):
        return None

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


# build_opener keeps its other default handlers (proxy, HTTPS, the error
# handlers) and leaves out its own redirect handler, which _NoRedirect subclasses.
_OPENER = urllib.request.build_opener(_NoRedirect)


def _send(body, key, timeout=TIMEOUT_S):
    """One HTTPS POST through _OPENER -> (status, payload). An HTTP error, a
    refused redirect included, keeps its status only."""
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json"})
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def ask(trace, step, send=_send, clock=time.perf_counter, key=None):
    """Ask jev about one second: {'model_name', 'ms', 'answers', 'sent'}.

    `key` is the page's key (SessionKey.get()): when given it is the key, and
    neither the environment nor the file is read; None means load_key(), as
    before. A key no HTTP header can carry is no key either way. `ms` is
    `clock` read around the call. JevError codes: no_key (before anything is
    sent), timeout, network, the STATUS_CODES names, vendor_status (with the
    status) and bad_answer.
    """
    if key is None:
        key, _source = load_key()
    if not key or not _header_safe(key):
        raise JevError("no_key")
    body = build_request(trace, step)
    start = clock()
    try:
        status, payload = send(body, key)
    except TimeoutError:
        raise JevError("timeout") from None
    except urllib.error.URLError as err:
        raise JevError("timeout" if isinstance(err.reason, TimeoutError) else "network") from None
    except (OSError, http.client.HTTPException):
        raise JevError("network") from None
    ms = (clock() - start) * 1000.0
    if status in STATUS_CODES:
        raise JevError(STATUS_CODES[status])
    if not 200 <= status < 300:
        raise JevError("vendor_status", int(status))
    try:
        data = json.loads(payload)
        answers = to_action(data.get("answers") if isinstance(data, dict) else None)
    # BadAnswer and bad JSON are ValueErrors. A huge integer overflows in
    # to_action and deep nesting exhausts json.loads: the reply, all of them.
    except (ValueError, OverflowError, RecursionError):
        raise JevError("bad_answer") from None
    name = data.get("model")
    return {"model_name": name if isinstance(name, str) and len(name) <= 64 else None,
            "ms": round(ms, 1), "answers": answers, "sent": body}

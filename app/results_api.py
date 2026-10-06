"""The results tab's two routes: GET /results (the page) and GET /api/results (its data).

Imported only from the --simulation branch of app/server.py, which calls
mount_results(app) right after app.agent_api.install(app), so --live and
--replay never load the readers, which import agent code through
app.agent_catalog. The function is not named install, so the route pin on a
single install( call in server.py still holds.

Mounting imports app.results_provenance and no other module of the tab. Its
plant hash is taken when it is imported, and the server loaded the plant
when it started, so the hash is taken then too: taken at the first request
instead, a plant file edited in between would read as the plant the server
runs (spec 5.2).

Both routes are GETs and synchronous: FastAPI runs them in its thread pool,
so a build never blocks the event loop, and one module-level lock lets one
build run at a time; a second request waits for it. Both answer
Cache-Control: no-store, the refusal included.

THE GUARD. A request whose raw Host header is not 127.0.0.1 or localhost,
with any port or none, gets a fixed-text refusal: that stops DNS rebinding.
No Origin is required, because a browser sends none on a same-origin GET.
The pattern is app.agent_api.LOCAL_HOST's, copied rather than imported
(importing it would load agent code) and widened to a host with no port.

Neither route takes a parameter, so nothing from a request reaches the
filesystem. A failure outside every section answers a server error with a
fixed text naming the exception's type, never str(exc); its traceback goes
to uvicorn's error log, which the server's log level still prints, so a
failed build leaves a trace on the server while the browser still sees only
the type's name.
"""
import logging
import re
import threading
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost)(:\d{1,5})?$")
NO_STORE = {"Cache-Control": "no-store"}
PAGE = Path(__file__).resolve().parent / "static" / "results.html"
_LOCK = threading.Lock()


def host_ok(request) -> bool:
    """True when the raw Host header names this machine, with any port or none."""
    return LOCAL_HOST.fullmatch(request.headers.get("host") or "") is not None


def _refused():
    return PlainTextResponse("refused: this page answers 127.0.0.1 and localhost only",
                             status_code=403, headers=NO_STORE)


def mount_results(app, build=None) -> None:
    """Add GET /results and GET /api/results to `app`.

    `build` replaces app.results_data.build; tests pass a stand-in. The
    default is imported inside the handler, on the first request, so
    mounting loads no reader. The plant hash is taken here, when mounting:
    see the module docstring.
    """
    from app import results_provenance  # noqa: F401  (its plant hash, taken now)

    def results_page(request: Request):
        """The tab's frame, read from app/static/results.html on every request."""
        if not host_ok(request):
            return _refused()
        return HTMLResponse(PAGE.read_text(encoding="utf-8"), headers=NO_STORE)

    def results_answer(request: Request):
        """Every section, rebuilt from the files, one build at a time."""
        if not host_ok(request):
            return _refused()
        try:
            with _LOCK:
                if build is None:
                    from app.results_data import build as run
                else:
                    run = build
                return JSONResponse(run(), headers=NO_STORE)
        except (Exception, SystemExit) as exc:
            logging.getLogger("uvicorn.error").exception("results build failed")
            return JSONResponse({"detail": f"results failed: {type(exc).__name__}"},
                                status_code=500, headers=NO_STORE)

    app.add_api_route("/results", results_page, methods=["GET"],
                      response_class=HTMLResponse)
    app.add_api_route("/api/results", results_answer, methods=["GET"])

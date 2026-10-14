"""Read-only, app-owned artifact polling. Sync routes run outside the event loop."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import re
import threading
import time

from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse

LOCAL_HOST = re.compile(r'^(127\.0\.0\.1|localhost)(:\d{1,5})?$')
NO_STORE = {'Cache-Control': 'no-store'}


class ArtifactService:
    """Coalesce clients into at most one scan every two monotonic seconds."""
    def __init__(self, catalog, *, clock=time.monotonic):
        self.catalog = catalog
        self.clock = clock
        self._lock = threading.Lock()
        self._next_scan = float('-inf')
        self._scanning = False
        self._last_success = None
        self._error = None

    def refresh(self):
        if self.clock() < self._next_scan or not self._lock.acquire(blocking=False):
            return self.status()
        try:
            if self.clock() < self._next_scan:
                return self.status()
            self._scanning = True
            try:
                self.catalog.scan()
                self._last_success = datetime.now(timezone.utc).isoformat()
                self._error = None
            except (OSError, ValueError) as exc:
                self._error = type(exc).__name__
            finally:
                self._next_scan = self.clock() + 2.0
                self._scanning = False
            return self.status()
        finally:
            self._lock.release()

    def status(self):
        snapshot = self.catalog.snapshot()
        return self._status_for(snapshot)

    def _status_for(self, snapshot):
        revisions = {key: snapshot[key] for key in (
            'revision', 'training_revision', 'results_revision', 'plant_revision',
            'updating', 'training_updating', 'results_updating', 'plant_updating',
            'restart_needed') if key in snapshot}
        return dict(revisions, updating=bool(self._scanning or snapshot.get('updating')),
                    training_updating=bool(snapshot.get('training_updating')),
                    results_updating=bool(snapshot.get('results_updating', snapshot.get('updating'))),
                    last_success_at=self._last_success,
                    restart_needed=bool(snapshot.get('restart_needed')),
                    error=self._error)

    def published(self):
        self.refresh()
        snapshot = deepcopy(self.catalog.snapshot())
        return dict(snapshot, **self._status_for(snapshot))


def mount_artifacts(app, service=None):
    """Called only by simulation startup; no route accepts filesystem paths."""
    if service is None:
        from app.artifact_catalog import ArtifactCatalog
        service = ArtifactService(ArtifactCatalog(Path(__file__).resolve().parent.parent))
    app.state.artifacts = service

    def refusal(request):
        if LOCAL_HOST.fullmatch(request.headers.get('host') or '') is None:
            return PlainTextResponse('refused: localhost only', status_code=403, headers=NO_STORE)
        return None

    def snapshot(request: Request):
        denied = refusal(request)
        if denied is not None:
            return denied
        return JSONResponse(service.published(), headers=NO_STORE)

    def revision(request: Request):
        denied = refusal(request)
        if denied is not None:
            return denied
        return JSONResponse(service.refresh(), headers=NO_STORE)

    app.add_api_route('/api/artifacts', snapshot, methods=['GET'])
    app.add_api_route('/api/artifacts/revision', revision, methods=['GET'])
    return service

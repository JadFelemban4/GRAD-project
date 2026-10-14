/** Poll the lightweight artifact revision endpoint without overlapping reads. */
export function createArtifactSync({
  readRevision,
  onChange,
  onStatus = () => {},
  schedule = setTimeout,
  cancel = clearTimeout,
  isVisible = () => !document.hidden,
}) {
  let active = false;
  let generation = 0;
  let timer = null;
  let controller = null;
  let flight = null;
  let inFlight = false;
  let resumePending = false;
  let previous = null;
  let lastSuccessAt = null;
  let failures = 0;

  const status = state => {
    try { onStatus({ state, lastSuccessAt }); } catch { /* status rendering cannot break polling */ }
  };

  const clearTimer = () => {
    if (timer !== null) cancel(timer);
    timer = null;
  };

  const queue = (token, delay) => {
    if (!active || token !== generation || !isVisible()) return;
    clearTimer();
    timer = schedule(() => {
      timer = null;
      void poll(token);
    }, delay);
  };

  const revisionsChanged = (before, after) => before === null
    || ['revision', 'training_revision', 'results_revision', 'plant_revision']
      .some(key => after?.[key] !== before?.[key]);

  async function poll(token) {
    if (!active || token !== generation || !isVisible() || inFlight) return;
    inFlight = true;
    const request = new AbortController();
    controller = request;
    flight = request;
    try {
      const next = await readRevision(request.signal);
      if (!active || token !== generation || controller !== request || request.signal.aborted) return;
      if (next?.error) throw new Error(String(next.error));

      const changed = revisionsChanged(previous, next);
      const needsRetry = Boolean(next?.updating) || Boolean(previous?.updating);
      if (changed || needsRetry) await onChange(previous, next, { signal: request.signal });
      if (!active || token !== generation || controller !== request || request.signal.aborted) return;

      previous = next;
      lastSuccessAt = next?.last_success_at ?? lastSuccessAt;
      failures = 0;
      status(next?.updating ? 'updating' : 'connected');
      queue(token, 2000);
    } catch (error) {
      if (!active || token !== generation || controller !== request || request.signal.aborted) return;
      failures += 1;
      status('offline');
      const delays = [2000, 4000, 8000, 30000];
      queue(token, delays[Math.min(failures - 1, delays.length - 1)]);
    } finally {
      if (controller === request) {
        controller = null;
      }
      if (flight === request) {
        flight = null;
        inFlight = false;
        if (resumePending && active && isVisible()) {
          resumePending = false;
          void poll(generation);
        }
      }
    }
  }

  function start() {
    if (active) return;
    active = true;
    generation += 1;
    previous = null;
    failures = 0;
    if (isVisible()) void poll(generation);
  }

  function stop() {
    if (!active) return;
    active = false;
    generation += 1;
    clearTimer();
    controller?.abort();
    controller = null;
    flight = null;
    inFlight = false;
    resumePending = false;
  }

  function visibilityChanged() {
    if (!active) return;
    if (!isVisible()) {
      clearTimer();
      controller?.abort();
      controller = null;
      return;
    }
    clearTimer();
    if (inFlight) resumePending = true;
    else void poll(generation);
  }

  return { start, stop, visibilityChanged };
}

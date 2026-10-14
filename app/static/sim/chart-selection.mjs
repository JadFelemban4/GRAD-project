// A cursor belongs to one source generation and one axis. No index translation.
export function createChartSelection({ sourceRevision, axisKind }) {
  const empty = () => Object.freeze({ sourceRevision, axisKind, sampleIndex:null, pairSeed:null });
  let current = empty();
  const listeners = new Set();
  const publish = next => {
    if (next.sampleIndex === current.sampleIndex && next.pairSeed === current.pairSeed) return;
    current = Object.freeze(next);
    for (const listener of listeners) listener(current);
  };
  return {
    get: () => current,
    set(next) {
      if (next.sourceRevision !== sourceRevision || next.axisKind !== axisKind) return false;
      if (next.sampleIndex != null && (!Number.isInteger(next.sampleIndex) || next.sampleIndex < 0)) return false;
      if (next.pairSeed != null && !['string','number'].includes(typeof next.pairSeed)) return false;
      publish({ sourceRevision, axisKind, sampleIndex:next.sampleIndex ?? null, pairSeed:next.pairSeed ?? null });
      return true;
    },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    reset() { publish(empty()); },
  };
}

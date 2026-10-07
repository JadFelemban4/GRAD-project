const nodes = ['t_block', 't_oil', 't_turb'];
const finite = value => typeof value === 'number' && Number.isFinite(value);
function freeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
export function snapshot(request, response) {
  return freeze(structuredClone({ request, frames: response.frames, method: response.method, initial_state: response.initial_state }));
}
export function comparison(reference, current) {
  if (!reference || !current) return { valid: false, changed: [], invalid: ['missing'] };
  const changed = Object.keys(reference.request).filter(key => reference.request[key] !== current.request[key]);
  const invalid = changed.filter(key => !['fan', 'pump'].includes(key));
  if (reference.method !== current.method) invalid.push('method');
  if (reference.initial_state !== current.initial_state) invalid.push('initial_state');
  const a = reference.frames[0], b = current.frames[0];
  if (!a || !b || ['time_s', ...nodes].some(key => !finite(a[key]) || !finite(b[key]) || a[key] !== b[key])) invalid.push('initial_frame');
  return { valid: invalid.length === 0, changed, invalid };
}
export function sharedAt(reference, current, time) {
  const a = reference.find(frame => frame.time_s === time);
  const b = current.find(frame => frame.time_s === time);
  if (!a || !b) return null;
  return { time, values: Object.fromEntries(nodes.map(key => {
    const reference = finite(a[key]) ? a[key] - 273.15 : null;
    const current = finite(b[key]) ? b[key] - 273.15 : null;
    return [key, { reference, current, delta: reference !== null && current !== null ? current - reference : null }];
  })) };
}
export function axis(reference, current, node) {
  const all = [...reference, ...current];
  const values = all.filter(frame => finite(frame[node])).map(frame => frame[node] - 273.15);
  const lo = values.length ? Math.min(...values) : 0;
  const hi = values.length ? Math.max(...values) : 0;
  const pad = Math.max(1, (hi - lo) * .06);
  const times = all.filter(frame => finite(frame.time_s)).map(frame => frame.time_s);
  return { min: lo - pad, max: hi + pad, timeMax: Math.max(1, ...times) };
}
export function restoreReference(reference) { return { run: reference, draft: { ...reference.request } }; }
export function requestGate() {
  let generation = 0;
  return { begin: () => ++generation, accept: version => version === generation, cancel: () => { generation++; } };
}

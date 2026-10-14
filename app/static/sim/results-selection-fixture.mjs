// Test-only browser boundary for exercising the real results page module.
import assert from 'node:assert/strict';
import { FakeEl } from './charts-fake-dom.mjs';

class Node extends FakeEl {
  constructor(tag) { super(tag); this.dataset = {}; this.listeners = {}; this.value = ''; this.checked = false; }
  append(...nodes) { for (const node of nodes) this.appendChild(node); }
  removeAttribute(name) { delete this.attrs[name]; }
  insertBefore(node, before) {
    if (!before) return this.appendChild(node);
    if (node === before) return node;
    node.remove();
    this.children.splice(this.children.indexOf(before), 0, node);
    node.parentNode = this;
    return node;
  }
  focus() { document.activeElement = this; }
  scrollIntoView() {}
  closest() { return null; }
  querySelector(selector) { return ['use', 'span'].includes(selector) ? null : super.querySelector(selector); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
}

let instance = 0;
export const settle = () => new Promise(resolve => setTimeout(resolve, 20));
export const agentSet = id => ({ id, kind: 'agent_set', name: id, relative_path: `results/agents/${id}`,
  lifecycle: 'finished', coherence: 'current', capabilities: { evaluation_summary: true },
  members: [], source_files: [], issues: [] });
export const evaluation = id => ({ id: `exp-${id}`, prefix: id, state: 'unavailable',
  error: { kind: 'read', file: `results/${id}_seed0.txt`, type: 'NotEvaluationFile' } });
export const snapshot = (revision, { sections = [], items = [], updating = false } = {}) => ({
  sections, not_read: [], built: {}, import_failures: [], updating,
  artifacts: { revision, results_revision: revision, plant_revision: 'plant', items },
});

export async function startResultsPage(t, hash = '') {
  const ids = ['error', 'built', 'warnings', 'summary', 'summary-rows', 'sections', 'not-read', 'not-read-list',
    'artifact-status', 'artifact-list', 'experiment-controls', 'experiment-select', 'compare-control',
    'compare-enabled', 'compare-field', 'compare-select', 'theme-toggle', 'lang-toggle'];
  const nodes = Object.fromEntries(ids.map(id => [id, new Node(id.includes('select') ? 'select' : 'div')]));
  const events = {};
  globalThis.document = {
    documentElement: new Node('html'), activeElement: null, hidden: false,
    createElement: tag => new Node(tag),
    getElementById: id => nodes[id] || nodes.sections.children.find(node => node.id === id) || null,
    querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
  };
  globalThis.window = { scrollY: 0, scrollBy() {}, matchMedia: () => ({ matches: false }),
    addEventListener: (name, callback) => { events[name] = callback; } };
  globalThis.location = { hash };
  globalThis.history = { scrollRestoration: 'auto',
    replaceState: (_state, _title, nextHash) => { location.hash = nextHash; },
    pushState: (_state, _title, nextHash) => { location.hash = nextHash; } };
  globalThis.localStorage = globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
  globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
  const requests = [];
  globalThis.fetch = (url, init) => new Promise((resolve, reject) => requests.push({ url, init, resolve, reject }));
  async function next() {
    const deadline = Date.now() + 2600;
    while (!requests.length && Date.now() < deadline) await settle();
    assert.ok(requests.length, 'results boot or refresh request was sent');
    return requests.shift();
  }
  const reply = (request, body) => request.resolve({ status: 200, json: async () => body });
  async function refresh(body) {
    const poll = await next();
    assert.equal(poll.url, '/api/artifacts/revision');
    reply(poll, { ...body.artifacts, updating: body.updating });
    const request = await next();
    assert.equal(request.url, '/api/results');
    reply(request, body);
    await settle();
  }
  t.after(() => events.pagehide?.());
  await import(`./results.mjs?selection-test=${++instance}`);
  return { nodes, events, next, reply, refresh };
}

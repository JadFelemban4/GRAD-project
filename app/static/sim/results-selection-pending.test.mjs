import test from 'node:test';
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
globalThis.location = { hash: '' };
globalThis.history = { scrollRestoration: 'auto', replaceState: (_state, _title, hash) => { location.hash = hash; },
  pushState: (_state, _title, hash) => { location.hash = hash; } };
globalThis.localStorage = globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
const requests = [];
globalThis.fetch = (url, init) => new Promise((resolve, reject) => requests.push({ url, init, resolve, reject }));
const settle = () => new Promise(resolve => setTimeout(resolve, 20));
async function next() {
  const deadline = Date.now() + 1800;
  while (!requests.length && Date.now() < deadline) await settle();
  assert.ok(requests.length, 'results boot or refresh request was sent');
  return requests.shift();
}
const reply = (request, body) => request.resolve({ status: 200, json: async () => body });
await import('./results.mjs');

test('cold boot waits through a pending-only catalog snapshot before choosing an available evaluation', async t => {
  t.after(() => events.pagehide?.());
  const pending = await next();
  reply(pending, {
    sections: [], not_read: [], built: {}, import_failures: [], updating: true,
    artifacts: { revision: 'pending', results_revision: 'pending', plant_revision: 'plant', items: [
      { id: 'agents', kind: 'agent_set', relative_path: 'results/agents', lifecycle: 'running',
        coherence: 'error', capabilities: {}, members: [], source_files: [], issues: [] },
    ] },
  });
  await settle();
  assert.equal(nodes['experiment-select'].value, '', 'an automatic pending registry placeholder is not selected');
  assert.equal(location.hash, '', 'automatic pending state does not write a deep link');
  assert.match(nodes['experiment-select'].children[1].textContent, /جارٍ التحقق/,
    'pending choices remain available and labeled while waiting');

  const poll = await next();
  assert.equal(poll.url, '/api/artifacts/revision');
  reply(poll, { revision: 'stable', results_revision: 'stable', plant_revision: 'plant', updating: false });
  const refresh = await next();
  assert.equal(refresh.url, '/api/results');
  reply(refresh, {
    sections: [{ id: 'exp-d2', prefix: 'd2', state: 'unavailable', error: { kind: 'read', type: 'NotEvaluationFile' } }],
    not_read: [], built: {}, import_failures: [], updating: false,
    artifacts: { revision: 'stable', results_revision: 'stable', plant_revision: 'plant', items: [
      { id: 'agents', kind: 'agent_set', relative_path: 'results/agents', lifecycle: 'finished',
        coherence: 'current', capabilities: { evaluation_summary: true }, members: [], source_files: [], issues: [] },
    ] },
  });
  await settle();
  assert.equal(nodes['experiment-select'].value, 'exp-d2', 'the evaluation choice is preferred over the now-ready set');
  assert.equal(location.hash, '#exp-d2');
});

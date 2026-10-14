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
  const deadline = Date.now() + 1500;
  while (!requests.length && Date.now() < deadline) await settle();
  assert.ok(requests.length, 'results boot request was sent');
  return requests.shift();
}
const payload = {
  sections: [],
  not_read: [], built: {}, import_failures: [], updating: false,
  artifacts: { revision: 'one', results_revision: 'one', plant_revision: 'plant', items: [
    { id: 'art_agents', kind: 'agent_set', relative_path: 'results/agents/agents', lifecycle: 'finished', coherence: 'current',
      capabilities: { evaluation_summary: true }, members: [], source_files: [], issues: [] },
    { id: 'art_second', kind: 'agent_set', relative_path: 'results/agents/second', lifecycle: 'finished', coherence: 'current',
      capabilities: { evaluation_summary: true }, members: [], source_files: [], issues: [] },
  ] },
};
await import('./results.mjs');

test('a coherent set-only snapshot selects and persists its registry choice', async t => {
  t.after(() => events.pagehide?.());
  const request = await next();
  request.resolve({ status: 200, json: async () => payload });
  await settle();
  assert.equal(nodes['experiment-select'].value, 'set:art_agents');
  assert.equal(location.hash, '#set:art_agents');
  assert.equal(nodes.sections.children[0].id, 'registry-selection');
  location.hash = '#set:art_agents';
  events.popstate();
  assert.equal(nodes['experiment-select'].value, 'set:art_agents', 'history navigation restores the registry fragment');
  await t.test('switching registry sets A to B to A displays only the selected set', () => {
    const first = nodes.sections.children[0];
    nodes['experiment-select'].value = 'set:art_second';
    nodes['experiment-select'].listeners.change();
    assert.equal(location.hash, '#set:art_second');
    assert.equal(nodes.sections.children.length, 1, 'the previous set is detached when selecting another set');
    assert.equal(nodes.sections.children[0].children[0].textContent, 'second');
    assert.equal(first.parentNode, null);

    const second = nodes.sections.children[0];
    nodes['experiment-select'].value = 'set:art_agents';
    nodes['experiment-select'].listeners.change();
    assert.equal(location.hash, '#set:art_agents');
    assert.deepEqual(nodes.sections.children.map(node => node.id), ['registry-selection']);
    assert.equal(nodes.sections.children[0], first, 'the first set is reused on return');
    assert.equal(second.parentNode, null);
  });
});

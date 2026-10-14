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
  querySelector(selector) { return selector === 'use' ? null : super.querySelector(selector); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
}
const nodes = Object.fromEntries(['sections', 'artifact-status', 'artifact-list', 'experiment-controls',
  'experiment-select', 'compare-control', 'compare-enabled', 'compare-field', 'compare-select', 'summary', 'summary-rows',
  'not-read', 'not-read-list'].map(id => [id, new Node(id.includes('select') ? 'select' : 'div')]));
const events = {};
globalThis.document = {
  documentElement: new Node('html'), activeElement: null, hidden: false,
  createElement: tag => new Node(tag),
  getElementById: id => nodes[id] || nodes.sections.children.find(x => x.id === id) || null,
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
};
globalThis.window = { scrollY: 0, scrollBy() {}, matchMedia: () => ({ matches: false }),
  addEventListener: (name, callback) => { events[name] = callback; } };
globalThis.location = { hash: '' };
globalThis.history = {
  pushState: (_state, _title, hash) => { location.hash = hash; },
  replaceState: (_state, _title, hash) => { location.hash = hash; },
};
globalThis.localStorage = globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
const requests = [];
globalThis.fetch = (url, init) => new Promise((resolve, reject) => requests.push({ url, init, resolve, reject }));
const settle = () => new Promise(resolve => setTimeout(resolve, 20));
async function next(ms = 2600) {
  const end = Date.now() + ms;
  while (!requests.length && Date.now() < end) await settle();
  assert.ok(requests.length, 'automatic refresh sends a request');
  return requests.shift();
}
const reply = (request, body) => request.resolve({ status: 200, json: async () => body });
const revision = name => ({ revision: name, training_revision: 'training', results_revision: name,
  plant_revision: 'plant', last_success_at: '2026-10-08T00:00:00Z', updating: false });
const section = name => ({ id: `exp-${name}`, prefix: name, state: 'unavailable',
  error: { kind: 'read', file: `results/${name}_seed0.txt`, type: 'NotEvaluationFile' } });
const source = prefix => ({ id: `results-${prefix}`, kind: 'evaluation_text', relative_path: `results/${prefix}_seed0.txt`,
  lifecycle: 'finished', capabilities: {}, source_files: [], issues: [] });
const payload = (name, sections, extraItems = []) => ({ artifacts: { ...revision(name),
  items: [...sections.map(item => source(item.prefix)), ...extraItems] }, source_revision: name,
  sections, not_read: [], built: {}, import_failures: [], updating: false });
await import('./results.mjs');

test('a boot reply after pagehide cannot publish or restart polling', async () => {
  const initial = await next();
  events.pagehide();
  reply(initial, payload('discarded', [section('discarded')]));
  await settle();
  assert.deepEqual(nodes.sections.children, []);
  assert.equal(requests.length, 0);
  events.pageshow();
});

test('Results keeps arrivals out of view until selected, scopes sources, and falls back after deletion', async t => {
  t.after(() => events.pagehide?.());
  const first = await next();
  assert.equal(first.url, '/api/results');
  reply(first, payload('one', [section('a')]));
  await settle();
  const a = nodes.sections.children[0];
  assert.equal(a.id, 'exp-a');
  assert.equal(nodes['experiment-select'].value, 'exp-a');
  assert.equal(nodes['artifact-list'].children.length, 1);
  const sourceA = nodes['artifact-list'].children[0];
  a.focus();
  const poll = await next();
  assert.equal(poll.url, '/api/artifacts/revision');
  reply(poll, revision('two'));
  const refresh = await next();
  assert.equal(refresh.url, '/api/results');
  const agentSet = { id: 'set-agents', kind: 'agent_set', relative_path: 'results/agents/agents',
    lifecycle: 'finished', coherence: 'current', capabilities: { model: true, evaluation_summary: true },
    members: [
      { name: 'agent-one', lifecycle: 'finished', capabilities: { model: true }, summary: { damage: { median: 12, worst: 18 } } },
      { name: 'agent-two', lifecycle: 'unknown', capabilities: { model: false }, summary: null },
    ], source_files: [], issues: [] };
  reply(refresh, payload('two', [section('a'), section('b')], [agentSet]));
  await settle();
  assert.equal(nodes.sections.children[0], a, 'unchanged section is reused');
  assert.equal(document.activeElement, a, 'arrival keeps the focused element');
  assert.deepEqual(nodes.sections.children, [a], 'arrival stays out of the selected results');
  assert.equal(nodes['experiment-select'].value, 'exp-a');
  assert.deepEqual(nodes['artifact-list'].children, [sourceA], 'arrival source stays out of view');
  nodes['experiment-select'].value = 'exp-b';
  nodes['experiment-select'].listeners.change();
  assert.deepEqual(nodes.sections.children.map(node => node.id), ['exp-b']);
  assert.equal(nodes['artifact-list'].children[0].children[0].children[0].textContent, 'results/b_seed0.txt');
  nodes['compare-enabled'].checked = true;
  nodes['compare-enabled'].listeners.change();
  nodes['compare-select'].value = 'exp-a';
  nodes['compare-select'].listeners.change();
  assert.deepEqual(nodes.sections.children.map(node => node.id), ['exp-b', 'exp-a'], 'second experiment appears only after opting in');
  assert.equal(location.hash, '#compare:exp-b:exp-a', 'comparison selection is represented in the URL');
  nodes['experiment-select'].value = 'exp-a';
  nodes['experiment-select'].listeners.change();
  assert.deepEqual(nodes.sections.children.map(node => node.id), ['exp-a'], 'changing primary clears a duplicate comparison');
  assert.equal(location.hash, '#exp-a');
  nodes['compare-select'].value = 'exp-b';
  nodes['compare-select'].listeners.change();
  assert.equal(location.hash, '#compare:exp-a:exp-b');
  nodes['experiment-select'].value = 'set:set-agents';
  nodes['experiment-select'].listeners.change();
  assert.equal(nodes.sections.children[0].id, 'registry-selection');
  assert.equal(location.hash, '#set:set-agents', 'registry selection replaces the stale evaluation fragment');
  assert.match(nodes.sections.children[0].textContent, /الضرر \(وحدات ضرر\)/);
  assert.match(nodes.sections.children[0].textContent, /الوسيط/);
  assert.match(nodes.sections.children[0].textContent, /12/);
  assert.match(nodes.sections.children[0].textContent, /ملفات منشورة/);
  assert.match(nodes.sections.children[0].textContent, /النموذج النهائي: متاح/);
  assert.match(nodes.sections.children[0].textContent, /لا يتوفر ملخص تقييم مسجَّل لهذا العضو/);
  assert.doesNotMatch(nodes.sections.children[0].textContent, /evaluation_summary|model:|\btrue\b|\bfalse\b/);
  assert.equal(nodes.summary.hidden, true, 'a registry set does not receive evaluation summary rows');
  assert.equal(nodes['artifact-list'].children.length, 1);
  assert.equal(nodes['artifact-list'].children[0].children[0].children[0].textContent, 'results/agents/agents');
  assert.doesNotMatch(nodes['artifact-list'].children[0].textContent, /بانتظار قارئ مجموعة الوكلاء|awaiting reader/);
  location.hash = '#compare:exp-b:exp-a';
  events.popstate();
  assert.deepEqual(nodes.sections.children.map(node => node.id), ['exp-b', 'exp-a'], 'Back restores both evaluation choices');
  location.hash = '#set:set-agents';
  events.popstate();
  assert.equal(nodes['experiment-select'].value, 'set:set-agents', 'Back restores the registry selection');
  const updatingSet = { ...agentSet, coherence: 'updating / last valid snapshot' };
  reply(await next(), revision('three'));
  reply(await next(), payload('three', [section('a'), section('b')], [updatingSet]));
  await settle();
  assert.equal(nodes['experiment-select'].value, 'set:set-agents', 'a selected set remains selected during refresh');
  assert.match(nodes.sections.children[0].textContent, /جارٍ التحديث · المعروض آخر نسخة سليمة/,
    'the last-valid state is visible in the selected registry summary');
  assert.match(nodes.sections.children[0].textContent, /12/, 'the last-valid summary values remain visible');
  reply(await next(), revision('four'));
  reply(await next(), payload('four', [section('a')]));
  await settle();
  assert.deepEqual(nodes.sections.children, [a]);
  assert.equal(nodes['experiment-select'].value, 'exp-a', 'deleted primary falls back to the first available experiment');
  const failed = await next();
  failed.reject(new TypeError('offline'));
  await settle();
  assert.deepEqual(nodes.sections.children, [a], 'disconnect retains the last snapshot');
  assert.match(nodes['artifact-status'].textContent, /غير متصل|Offline/i);
});

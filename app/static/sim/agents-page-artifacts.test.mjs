import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { installFakePage } from './agents-page-harness.mjs';

const h = installFakePage({ search: '?runs=runs_c4&seed=5&ep=1',
  ids: ['compute', 'pick-experiment', 'pick-pair', 'pick-episode', 'artifact-status', 'artifact-list'] });
const fixture = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const pageEvents = {};
window.addEventListener = (name, callback) => { pageEvents[name] = callback; };
document.addEventListener = () => {};
await import('./agents.mjs');

function catalog(revision, pairRevision = 'selected') {
  const body = structuredClone(fixture);
  body.source_revision = revision;
  body.artifacts = { revision, training_revision: revision, results_revision: 'r', plant_revision: 'p',
    items: [], updating: false, last_success_at: '2026-10-08T00:00:00Z' };
  body.experiments.find(x => x.runs === 'runs_c4').pairs.forEach(x => { x.source_revision = pairRevision; });
  return body;
}

test('a catalog boot reply after pagehide cannot restart polling', async () => {
  const initial = await h.nextRequest();
  pageEvents.pagehide();
  h.reply(initial, catalog('discarded'));
  await h.settle();
  assert.equal(h.requests.length, 0);
  assert.equal(h.nodes['pick-experiment'].value, '');
  pageEvents.pageshow();
});

test('open page discovers an unrelated arrival and preserves its selection, then pauses a replaced source', async () => {
  const pending = catalog('one');
  pending.artifacts.training_updating = true;
  pending.artifacts.updating = true;
  pending.experiments.find(x => x.runs === 'runs_c4').pairs.forEach(x => { x.runnable = false; });
  h.reply(await h.nextRequest(), pending);
  await h.settle();
  assert.equal(h.nodes['pick-experiment'].value, '');
  assert.equal(h.history.length, 0, 'an initial stability check cannot erase the incoming deep link');
  const revision = await h.nextRequest();
  assert.equal(revision.url, '/api/artifacts/revision');
  h.reply(revision, { revision: 'two', training_revision: 'two', results_revision: 'r', plant_revision: 'p' });
  const refresh = await h.nextRequest();
  assert.equal(refresh.url, '/api/agents/catalog');
  const next = catalog('two');
  next.experiments.push({ runs: 'art_' + 'a'.repeat(24), name: 'runs/new_set', pairs: [], verdict: {} });
  document.activeElement = h.nodes['pick-experiment'];
  h.reply(refresh, next);
  await h.settle();
  document.activeElement = h.nodes['pick-pair'];
  h.nodes['pick-experiment'].fire('blur');
  await h.settle();
  assert.ok(!h.nodes['pick-experiment'].children.some(x => x.value === 'art_' + 'a'.repeat(24)), 'focus handoff keeps the pending picker DOM');
  document.activeElement = null;
  h.nodes['pick-pair'].fire('blur');
  await h.settle();
  assert.equal(h.nodes['pick-experiment'].value, 'runs_c4');
  assert.equal(h.nodes['pick-pair'].value, '5');
  assert.equal(h.nodes['pick-episode'].value, '1');
  assert.ok(h.nodes['pick-experiment'].children.some(x => x.value === 'art_' + 'a'.repeat(24)));
  const changed = await h.nextRequest(4000);
  h.reply(changed, { revision: 'three', training_revision: 'three', results_revision: 'r', plant_revision: 'p' });
  h.reply(await h.nextRequest(), catalog('three', 'replacement'));
  await h.settle();
  assert.match(h.nodes['artifact-status'].textContent, /تغيّر مصدر|source changed/);
  pageEvents.pagehide();
});

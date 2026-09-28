// The /agents page opened from an address that names MORE than the catalog
// lets it select (episode 21 does not exist), against a fake DOM and a fake
// server (agents-page-harness.mjs). The page selects what it can, cuts the
// address back to exactly that, and computes nothing. This catalog also says
// stable-baselines3 is missing, as it is under the lab launcher's .venv: the
// page must say that nothing can be computed as soon as the catalog arrives,
// not after three choices.
//
// This file owns its own process, and agents.mjs boots once, on import; the
// tests run in order.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage } from './agents-page-harness.mjs';

const FIXTURE = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=21',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'lang-toggle'],
});
const { nodes } = h;
await import('./agents.mjs');

const AR = key => STRINGS.ar[key];
const times = (text, part) => text.split(part).length - 1;
const values = () => ['pick-experiment', 'pick-pair', 'pick-episode'].map(id => nodes[id].value);

test('an address naming more than exists is cut back to what it selects, and nothing computes', async () => {
  const boot = await h.nextRequest();
  assert.equal(boot.url, '/api/agents/catalog', 'the page\'s only request at boot is the catalog');
  h.reply(boot, { ...FIXTURE, sb3: false });
  await h.settle();
  assert.deepEqual(values(), ['runs_c4', '5', ''], 'the experiment and the pair exist; episode 21 does not');
  assert.deepEqual(h.history, ['/agents?runs=runs_c4&seed=5'], 'the address says only what is selected');
  assert.equal(nodes.compute.disabled, true);
  await h.settle();
  assert.equal(h.requests.length, 0, 'nothing computes');
});

// Starts from: runs_c4 / 5, no episode; the catalog says sb3 false.
test('without stable-baselines3 the picker says so once, before an episode is chosen and after', () => {
  const note = () => nodes['pick-note'].textContent;
  assert.equal(times(note(), AR('agents.load.no_sb3')), 1, 'said as soon as the catalog arrives');
  h.change(nodes['pick-episode'], '1');
  assert.deepEqual(values(), ['runs_c4', '5', '1']);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5&ep=1');
  assert.equal(nodes.compute.disabled, true, '«احسب» stays disabled');
  assert.equal(times(note(), AR('agents.load.no_sb3')), 1, 'said once at a full selection too, not twice');
  nodes.compute.click();
  assert.equal(h.requests.length, 0, 'a disabled «احسب» sends nothing');
});

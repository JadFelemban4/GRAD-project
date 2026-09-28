// The /agents page opened from its own nav link (no address), RUNNING against
// a fake DOM and a fake server (agents-page-harness.mjs). Jad found on 28 Sep
// that M1's page could not be used from the link at all: nothing selected and
// three read-only lists. These tests drive the picker the way a viewer does.
//
// This file owns its own process (node --test runs each file in one), and
// agents.mjs boots once, on import. The tests run IN ORDER and each says the
// selection it starts from: the page's state carries from one to the next.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage, byClass } from './agents-page-harness.mjs';

// Generated from the server's own catalog (agent_api.catalog). This file
// changes two things in a copy, both shaped as agent_catalog returns them, so
// the page meets a verdict that is not found: runs_d2's verdict is 'missing'
// (as if results/PHASE_D2_RESULT.txt were gone), and a runs_zz directory with
// no recorded verdict ('none') holds one runnable pair and one refused by a
// plant mismatch. sb3 is pinned true so nothing depends on the machine.
const FIXTURE = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const MISSING = {
  ar: 'لم يُعثر على سطر الحكم في results/PHASE_D2_RESULT.txt: لا تقرأ هؤلاء الوكلاء بدونه',
  en: 'verdict line not found in results/PHASE_D2_RESULT.txt: do not read these agents without it',
};
const NONE = {
  ar: 'لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.',
  en: 'No preregistered verdict for this experiment in results/. Nothing on this page is a result.',
};
const CATALOG = structuredClone({ ...FIXTURE, sb3: true });
const D2 = CATALOG.experiments.find(e => e.runs === 'runs_d2');
D2.verdict = { state: 'missing', lines: [], missing: ['PHASE_D2_RESULT.txt'], short: MISSING, cells: [] };
const MISMATCH = [
  'blind_seed9: incompatible -- plant mismatch: plant_sha',
  "blind_seed9: plant_sha: stored 'aaaa' live 'bbbb'",
];
CATALOG.experiments.push({
  runs: 'runs_zz', name: 'runs_zz (no name recorded)', prefix: 'zz', protocol: 'd2',
  verdict: { state: 'none', lines: [], missing: [], short: NONE, cells: [] },
  pairs: [
    structuredClone(D2.pairs[0]),
    { ...structuredClone(D2.pairs[1]), seed: 9, runnable: false, reason: MISMATCH[0], problems: MISMATCH,
      protocol: null, table_diff: null },
  ],
});
const C4 = CATALOG.experiments.find(e => e.runs === 'runs_c4');

const h = installFakePage({
  search: '',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'pick-pair-note',
    'pick-episode-note', 'pick-refused', 'verdict', 'verdict-short', 'verdict-cells', 'strip-verdict',
    'verdict-scored', 'scene-prompt', 'pause-heading', 'loading', 'load-title', 'lane-blind-label', 'seen-blind',
    'lane-stopped', 'lang-toggle', 'seek', 'sim-badge'],
});
const { nodes } = h;
await import('./agents.mjs');

const AR = key => STRINGS.ar[key];
const options = select => select.children.map(o => ({ value: o.value, text: o.textContent, disabled: o.disabled }));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

// One meta and one road for runs_c4 seed 5 episode 1, shaped as
// agent_api.episode_meta and agent_trace.route send them.
const c4Pair = seed => C4.pairs.find(p => p.seed === seed);
const META = {
  experiment: 'C4', runs: 'runs_c4', prefix: 'c4', protocol: 'd2', seed: 5, ep: 1,
  episode: { ...CATALOG.episodes.d2[0] }, dt: 1, steps: 719,
  train_dt: { sighted: 0.2, blind: 0.2 }, agents: c4Pair(5).agents, result_file: true,
  preview_s: CATALOG.preview_s, act: CATALOG.act, limits: CATALOG.limits,
  scenario: { v_kmh: 130, t_amb_c: 42, p_baro_kpa: 101.3 }, verdict: C4.verdict,
};
const ROAD = {
  rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};
const car = (over = {}) => ({
  cmd: [0, 0, 0, 1, 1], act: [0, 0, 0, 1, 1], held: [false, false, false, false, false],
  preview_pct: [0, 0, 12, 12], map_kpa: 180, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5,
  ...over,
});

// The boot request, failed. The note under the selects must stop saying the
// list is loading; the retry asks for the catalog again, and the next test
// answers that request.
test('a catalog request that fails says so under the selects, and its retry asks again', async () => {
  const first = await h.nextRequest();
  assert.equal(first.url, '/api/agents/catalog');
  h.fail(first);
  await h.settle();
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.catalog_failed'), 'not «تحميل قائمة التجارب…» any more');
  assert.equal(nodes['pick-experiment'].disabled, true, 'nothing can be chosen without the catalog');
  assert.equal(nodes.compute.disabled, true);
  const retry = nodes.error.children.find(c => c.tagName === 'button');
  assert.ok(retry, 'the error offers a retry');
  retry.click();
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.catalog_loading'), 'retrying, the list is loading again');
  assert.equal(nodes.error.hidden, true);
});

// Starts from: the catalog asked for again by the retry, not yet answered.
test('from the nav link the page selects nothing, computes nothing, and says what to choose', async () => {
  const first = await h.nextRequest();
  assert.equal(first.url, '/api/agents/catalog', 'the page\'s only request at boot is the catalog');
  assert.equal(nodes['pick-experiment'].disabled, true, 'nothing can be chosen before the catalog arrives');
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.catalog_loading'));
  h.reply(first, CATALOG);
  await h.settle();

  const exp = options(nodes['pick-experiment']);
  assert.deepEqual(exp.map(o => o.value), ['', 'runs', 'runs_c4', 'runs_d2', 'runs_sixspeed_18sep', 'runs_zz']);
  assert.equal(exp[0].text, AR('agents.pick.choose'));
  assert.equal(nodes['pick-experiment'].value, '', 'no experiment is chosen for the viewer');
  assert.equal(nodes['pick-experiment'].disabled, false);
  const sixspeed = exp.find(o => o.value === 'runs_sixspeed_18sep');
  assert.equal(sixspeed.disabled, true, 'a directory with no runnable pair is greyed');
  assert.match(sixspeed.text, /no meta\.json/, 'and says why');
  assert.equal(nodes['pick-pair'].disabled, true);
  assert.equal(nodes['pick-episode'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.none'));
  assert.equal(nodes['scene-prompt'].hidden, false);
  assert.equal(nodes['verdict-short'].textContent, '—', 'no verdict before an experiment is chosen');
  await wait(450);
  assert.equal(h.requests.length, 0, 'nothing computes');
  assert.deepEqual(h.history, [], 'the address is left as it was');
});

// Starts from: nothing selected.
test('every pair that cannot run is listed with every problem the server found, both arms and each field', () => {
  const box = nodes['pick-refused'];
  assert.equal(box.hidden, false);
  const summary = box.children.find(c => c.tagName === 'summary');
  assert.equal(summary.textContent, AR('agents.pick.refused_summary').replace('{n}', '2'));
  const items = byClass(box, 'refused-pair').map(item => item.textContent);
  assert.equal(items.length, 2, 'runs_sixspeed_18sep seed 0 and runs_zz seed 9');
  assert.ok(items[0].includes('sighted_seed0: incompatible -- no meta.json'), items[0]);
  assert.ok(items[0].includes('blind_seed0: incompatible -- no meta.json'), 'the second arm too, which no option shows');
  assert.ok(items[1].includes("plant_sha: stored 'aaaa' live 'bbbb'"), 'and each stored and live field');
  const lists = byClass(box, 'refused-pair').flatMap(item => item.children.filter(c => c.tagName === 'ul'));
  assert.ok(lists.every(list => list.dir === 'ltr'), 'the problems read left to right');
  assert.equal(lists.flatMap(list => list.children).length, 4, 'two problems for each refused pair');
});

// Starts from: nothing selected.
test('a refused experiment is greyed with its reason and cannot be chosen', async () => {
  h.change(nodes['pick-experiment'], 'runs_sixspeed_18sep');
  await h.settle();
  assert.equal(nodes['pick-experiment'].value, '', 'the select falls back to its placeholder');
  assert.equal(nodes['pick-pair'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.deepEqual(h.history, [], 'a choice that selects nothing leaves the address alone');
  assert.equal(h.requests.length, 0);
});

// Starts from: nothing selected.
test('a verdict that is missing, or was never recorded, says so in the box, the strip and the select', () => {
  const experiment = runs => options(nodes['pick-experiment']).find(o => o.value === runs);
  h.change(nodes['pick-experiment'], 'runs_d2');
  assert.equal(nodes.verdict.dataset.state, 'missing');
  assert.equal(nodes['verdict-short'].textContent, MISSING.ar);
  assert.equal(nodes['strip-verdict'].textContent, MISSING.ar);
  assert.ok(experiment('runs_d2').text.endsWith(MISSING.ar), 'the experiment select says it too');
  assert.equal(nodes['verdict-cells'].children.length, 0, 'a cell is never guessed');

  h.change(nodes['pick-experiment'], 'runs_zz');
  assert.equal(nodes.verdict.dataset.state, 'none');
  assert.equal(nodes['verdict-short'].textContent, NONE.ar);
  assert.equal(nodes['strip-verdict'].textContent, NONE.ar);
  assert.ok(experiment('runs_zz').text.endsWith(NONE.ar));
  assert.equal(nodes['verdict-cells'].children.length, 0);
  const pairs = options(nodes['pick-pair']);
  assert.equal(pairs.length, 3, 'the placeholder, the runnable pair and the refused one');
  assert.equal(pairs[2].disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_zz');
});

// Starts from: runs_zz, no pair.
test('each choice fills the next select, keeps the address in sync and enables «احسب» only at a full selection', async () => {
  h.change(nodes['pick-experiment'], 'runs_c4');
  const pairs = options(nodes['pick-pair']);
  assert.equal(pairs.length, 9, 'the placeholder and eight pairs');
  assert.equal(nodes['pick-pair'].disabled, false);
  assert.equal(nodes['pick-pair'].value, '', 'no pair is chosen for the viewer');
  assert.match(pairs[1].text, /360\.6/, 'seed 0 quotes its row of the results table');
  assert.equal(nodes['pick-pair-note'].textContent, AR('agents.pick.pair_qualifier'));
  assert.equal(nodes['verdict-short'].textContent, C4.verdict.short.ar, 'the box reads the chosen experiment');
  assert.equal(nodes['strip-verdict'].textContent, C4.verdict.short.ar);
  assert.equal(nodes.verdict.dataset.state, 'found');
  assert.equal(nodes['pick-episode'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4');

  h.change(nodes['pick-pair'], '5');
  assert.equal(options(nodes['pick-episode']).length, 21, 'the placeholder and twenty episodes');
  assert.equal(nodes['pick-episode'].disabled, false);
  assert.equal(byClass(nodes['pick-note'], 'sighted').length, 1, 'one budget line per arm');
  assert.equal(byClass(nodes['pick-note'], 'blind').length, 1, 'one budget line per arm');
  assert.match(nodes['pick-note'].textContent, /300\D000/, 'each arm says what it was trained for');
  assert.ok(nodes['pick-note'].textContent.endsWith(AR('agents.pick.need_episode')));
  // The verdict box names both arms of the chosen pair from the catalog,
  // before «احسب»: each is the artefact results/ scored (agent-picker.scoredKey).
  const scored = ['sighted', 'blind'].flatMap(lane => byClass(nodes['verdict-scored'], lane));
  assert.equal(scored.length, 2, 'one scored line per arm of the chosen pair');
  assert.ok(scored.every(li => li.textContent.includes(AR('agents.verdict.scored_match'))), 'each arm reads as scored');
  assert.equal(nodes.compute.disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5');

  h.change(nodes['pick-episode'], '1');
  assert.equal(nodes.compute.disabled, false);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5&ep=1');
  assert.match(nodes['pick-note'].textContent, /141/, 'the chosen episode is spelled out under the selects');
  await h.settle();
  assert.equal(h.requests.length, 0, 'nothing computes until «احسب»');
});

// Starts from: runs_c4 / 5 / 1.
test('«احسب» asks for exactly the chosen episode, once with preempt=1', async () => {
  nodes.compute.click();
  const req = await h.nextRequest();
  const url = new URL(req.url, 'http://localhost');
  assert.equal(url.pathname, '/api/agents/episode');
  assert.deepEqual(Object.fromEntries(url.searchParams),
    { runs: 'runs_c4', seed: '5', ep: '1', since: '0', preempt: '1' });
  h.reply(req, { status: 'building', since: 0, steps: 719, frames: [{ k: 0, cars: [car(), car()] }], meta: META, road: ROAD });
  const next = await h.nextRequest();
  assert.doesNotMatch(next.url, /preempt/, 'the polls after it wait their turn');
  assert.match(next.url, /since=1/);
  h.reply(next, { status: 'ready', since: 1, steps: 719, frames: [] });
  await h.settle();
});

// Starts from: runs_c4 / 5 / 1, computed.
test('changing the pair after a computation clears the old episode and drops its late frames', async () => {
  nodes.compute.click();
  h.reply(await h.nextRequest(), { status: 'building', since: 0, steps: 719, frames: [{ k: 0, cars: [car(), car()] }], meta: META, road: ROAD });
  const inFlight = await h.nextRequest();
  assert.notEqual(nodes['pause-heading'].textContent, '—', 'the episode is on screen');
  assert.equal(nodes['scene-prompt'].hidden, true);

  h.change(nodes['pick-pair'], '3');
  assert.equal(nodes['pause-heading'].textContent, '—', 'the old episode left the pause panel');
  assert.equal(nodes['scene-prompt'].hidden, false, 'the scene asks for «احسب» again');
  assert.equal(nodes.loading.hidden, true, 'no loading card for an episode nobody asked for');
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=3&ep=1', 'the episode is kept: the same twenty episodes');
  assert.equal(nodes['pick-episode'].value, '1');
  assert.equal(nodes.compute.disabled, false);

  h.reply(inFlight, { status: 'building', since: 1, steps: 719, frames: [{ k: 1, cars: [car(), car()] }] });
  await wait(450);
  assert.equal(nodes['pause-heading'].textContent, '—', 'a late frame of the old key changed the page');
  assert.equal(h.requests.length, 0, 'the old key is not polled again');
});

// Starts from: runs_c4 / 3 / 1, nothing computed.
test('Phase D: the same-road episodes, and the blind car named as possibly memorising its road wherever it is named', async () => {
  const PD = FIXTURE.experiments.find(e => e.runs === 'runs');
  h.change(nodes['pick-experiment'], 'runs');
  assert.equal(nodes['pick-pair-note'].textContent, AR('agents.pick.pair_qualifier_same_road'));
  assert.match(nodes['pick-episode-note'].textContent, /180/, 'the one road\'s climb start');
  assert.match(nodes['pick-episode-note'].textContent, /12\.0/, 'and its grade');
  h.change(nodes['pick-pair'], '0');
  const episodes = options(nodes['pick-episode']).slice(1);
  assert.equal(episodes.length, 20);
  assert.ok(episodes.every(o => o.text.includes('الطريق نفسه')), 'every Phase D episode says it is the same road');
  h.change(nodes['pick-episode'], '1');
  assert.match(byClass(nodes['pick-note'], 'blind')[0].textContent, /قد يحفظه/, 'the blind arm\'s budget line');
  assert.doesNotMatch(byClass(nodes['pick-note'], 'sighted')[0].textContent, /قد يحفظه/);
  assert.equal(nodes['verdict-short'].textContent, PD.verdict.short.ar);
  assert.match(byClass(nodes['verdict-scored'], 'blind')[0].textContent, /قد يحفظه/, 'the verdict box\'s scored line');

  nodes.compute.click();
  const req = await h.nextRequest();
  assert.match(req.url, /runs=runs&seed=0&ep=1&/);
  const meta = {
    ...META, experiment: 'Phase D', runs: 'runs', prefix: 'phase_d', protocol: 'phase-d', seed: 0, ep: 1,
    episode: { ...CATALOG.episodes['phase-d'][0] }, agents: PD.pairs[0].agents, verdict: PD.verdict,
  };
  const blind = car({ preview_pct: [0, 0, 0, 0] });
  h.reply(req, { status: 'ready', since: 0, steps: 2, meta, road: ROAD,
    frames: [{ k: 0, cars: [car(), blind] }, { k: 1, cars: [car(), null] }] });
  await h.settle();
  assert.match(nodes['lane-blind-label'].textContent, /قد يحفظه/, 'the scene label');
  assert.match(nodes['sim-badge'].textContent, /12\.0/, 'the badge reads the one road\'s grade');
  h.seekTo(0.5);
  assert.match(nodes['seen-blind'].textContent, /قد يحفظه/, 'the pause panel line');
  assert.ok(nodes['seen-blind'].textContent.includes('results/PHASE_D_RESULT.txt:33-40'), 'cited where results/ says it');
  assert.match(nodes['seen-blind'].textContent, /0 · 0 · 0 · 0/, 'with the inputs it was actually given');
  h.seekTo(1.5);
  assert.equal(nodes['lane-stopped'].hidden, false);
  assert.ok(nodes['lane-stopped'].textContent.startsWith(AR('agents.car.blind_phase_d')), 'the stopped lane');

  h.change(nodes['pick-experiment'], 'runs_c4');
  h.change(nodes['pick-pair'], '5');
  h.change(nodes['pick-episode'], '1');
  const c4Blind = byClass(nodes['pick-note'], 'blind')[0].textContent;
  assert.ok(c4Blind.startsWith(AR('agents.car.blind')), 'C4\'s blind car keeps its own label');
  assert.doesNotMatch(c4Blind, /قد يحفظه/, 'without the Phase D caveat');
});

// Starts from: runs_c4 / 5 / 1, nothing computed.
test('«احسب» over another running build says it is stopping it, not to press «احسب» again', async () => {
  const title = () => nodes['load-title'].textContent;
  const busy = { status: 'busy', since: 0, steps: 719, frames: [], active: { runs: 'runs_c4', seed: 3, ep: 1 } };
  nodes.compute.click();
  const req = await h.nextRequest();
  assert.match(req.url, /preempt=1/);
  h.reply(req, { ...busy, meta: META, road: ROAD });
  await h.settle();
  assert.match(title(), /يُوقَف/);
  for (const part of ['runs_c4', ' 3 ', ' 1)']) assert.ok(title().includes(part), `names the build it stops: ${part}`);
  assert.doesNotMatch(title(), /اضغط احسب/, 'this press already asked for it');

  const second = await h.nextRequest();
  assert.doesNotMatch(second.url, /preempt/);
  h.reply(second, busy);
  await h.settle();
  assert.match(title(), /يُوقَف/, 'still stopping it on the next poll');

  h.reply(await h.nextRequest(), { status: 'loading', since: 0, steps: 719, frames: [] });
  await h.settle();
  assert.equal(title(), AR('agents.load.networks'));

  h.fail(await h.nextRequest());
  await h.settle();
  const retry = nodes.error.children.find(c => c.tagName === 'button');
  assert.ok(retry, 'a failed poll offers a retry');
  retry.click();
  h.reply(await h.nextRequest(), busy);
  await h.settle();
  assert.match(title(), /اضغط احسب/, 'after a failed request the preempt may never have arrived');
});

// Each of the two ways «يُوقَف» ends, on its own (the test above passes through
// both at once). Starts from: runs_c4 / 5 / 1, a busy answer still polled.
test('«يُوقَف» ends once this page\'s own build answers, and when the «احسب» request itself fails', async () => {
  const title = () => nodes['load-title'].textContent;
  const busy = { status: 'busy', since: 0, steps: 719, frames: [], active: { runs: 'runs_c4', seed: 3, ep: 1 } };
  nodes.compute.click();
  h.reply(await h.nextRequest(), { status: 'loading', since: 0, steps: 719, frames: [] });
  await h.settle();
  h.reply(await h.nextRequest(), busy);
  await h.settle();
  assert.match(title(), /اضغط احسب/, 'its own build answered, so this build was started by someone else');

  nodes.compute.click();
  h.fail(await h.nextRequest());
  await h.settle();
  nodes.error.children.find(c => c.tagName === 'button').click();
  h.reply(await h.nextRequest(), busy);
  await h.settle();
  assert.match(title(), /اضغط احسب/, 'the «احسب» request failed, so its preempt may never have arrived');
});

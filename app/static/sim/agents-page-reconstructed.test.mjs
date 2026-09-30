// The /agents page showing a pair whose certificates were RECONSTRUCTED
// (reconstruct_meta.py; app/agent_catalog.py reconstructed_meta), against a
// fake DOM and a fake server (agents-page-harness.mjs).
//
// The twenty agents of the 29 September retrain were trained on a new road
// every episode, on the CPU, by a train.py that wrote no meta.json. Three
// sentences the page says of the closed experiments are false of them, and
// each is checked here against Phase D's own pair:
//  - the verdict box must say the certificate was reconstructed, when, and
//    against which committed scores, never "no result file for this pair";
//  - the blind car "may have memorised its one road" only where the agent
//    trained on one road;
//  - the device line must name the device the committed scores were
//    reproduced on, and warn only when this episode ran on another.
//
// This file owns its own process, and agents.mjs boots once, on import; the
// tests run in order.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage, byClass } from './agents-page-harness.mjs';

const FIXTURE = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const NONE = {
  ar: 'لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.',
  en: 'No preregistered verdict for this experiment in results/. Nothing on this page is a result.',
};
const SCORES = arm => `results/agents/terrain_dt1/${arm}_seed0/eval_summary.json`;
// One agent as agent_catalog.read_agent returns a reconstructed one.
const agent = arm => ({
  tag: `${arm}_seed0`, arm, status: 'ready', reason: null, problems: [],
  budget_line: 'trained 50000 steps of 50000 requested, from step 0, buffer 1000000, zip sha 0123456789abcdef',
  train_dt: 1, zip_sha: '0123456789abcdef', scored: 'not recorded', train_road: 'terrain',
  certificate: 'reconstructed',
  reconstructed: { written: '2026-09-30T17:20:00', reproduced_device: 'cpu', episodes: [1, 20], scores: SCORES(arm) },
});
const PAIR = {
  seed: 0, runnable: true, reason: null, problems: [], protocol: 'phase-d', result_file: false,
  table_diff: null, agents: [agent('sighted'), agent('blind')],
};
const CATALOG = structuredClone({ ...FIXTURE, sb3: true });
CATALOG.experiments.push({
  runs: 'runs_terrain_dt1', name: 'runs/terrain_dt1 (no name recorded)', prefix: 'terrain_dt1',
  protocol: 'phase-d', verdict: { state: 'none', lines: [], missing: [], short: NONE, cells: [] },
  pairs: [PAIR],
});

const h = installFakePage({
  search: '?runs=runs_terrain_dt1&seed=0',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'verdict',
    'verdict-short', 'verdict-scored', 'seen-blind', 'device-line', 'lang-toggle', 'seek'],
});
const { nodes } = h;
await import('./agents.mjs');

const AR = key => STRINGS.ar[key];
const lanes = node => ['sighted', 'blind'].flatMap(lane => byClass(node, lane));
const META = {
  experiment: 'runs/terrain_dt1 (no name recorded)', runs: 'runs_terrain_dt1', prefix: 'terrain_dt1',
  protocol: 'phase-d', seed: 0, ep: 1, episode: { ...CATALOG.episodes['phase-d'][0] }, dt: 1, steps: 719,
  train_dt: { sighted: 1, blind: 1 }, train_road: { sighted: 'terrain', blind: 'terrain' },
  agents: PAIR.agents, result_file: false, preview_s: CATALOG.preview_s, act: CATALOG.act,
  limits: CATALOG.limits, scenario: { v_kmh: 130, t_amb_c: 42, p_baro_kpa: 101.3 },
  verdict: CATALOG.experiments.at(-1).verdict,
};
const ROAD = {
  rise_m: 2340, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: 180,
  grade_pct: [0, 0, 12, 12], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 2, 4],
};
const car = () => ({
  cmd: [0, 0, 0, 1, 1], act: [0, 0, 0, 1, 1], held: [false, false, false, false, false],
  preview_pct: [0, 0, 0, 0], map_kpa: 180, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5,
});

test('the verdict box says each certificate was reconstructed, when, and against which scores', async () => {
  const boot = await h.nextRequest();
  assert.equal(boot.url, '/api/agents/catalog');
  h.reply(boot, CATALOG);
  await h.settle();
  assert.equal(nodes['pick-experiment'].value, 'runs_terrain_dt1', 'the set one level down is an experiment like any other');
  assert.equal(nodes['pick-pair'].value, '0');
  const scored = lanes(nodes['verdict-scored']);
  assert.equal(scored.length, 2, 'one line per arm');
  for (const [i, arm] of ['sighted', 'blind'].entries()) {
    const text = scored[i].textContent;
    assert.match(text, /أُعيد بناؤها/, `${arm}: the line must say the certificate was reconstructed`);
    assert.match(text, /لم تُكتب عند بدء التدريب/, `${arm}: and that it was not written when training started`);
    assert.ok(text.includes('2026-09-30'), `${arm}: the day it was reconstructed`);
    assert.ok(text.includes(SCORES(arm)), `${arm}: the committed scores it was re-run against`);
    assert.ok(text.includes('1, 20'), `${arm}: the frozen episodes that were re-run`);
    assert.ok(!text.includes(AR('agents.verdict.no_result')), `${arm}: its scores are committed, under results/agents/`);
  }
  assert.equal(nodes['verdict-short'].textContent, NONE.ar, 'and no preregistered verdict is claimed for it');
});

// Starts from: runs_terrain_dt1, seed 0, no episode.
test('a blind car trained on a new road every episode is not said to have memorised one', async () => {
  const blind = byClass(nodes['pick-note'], 'blind');
  assert.equal(blind.length, 1);
  assert.ok(blind[0].textContent.includes(AR('agents.car.blind')));
  assert.ok(!blind[0].textContent.includes('قد يحفظه'), `a terrain-trained agent had no one road to memorise: ${blind[0].textContent}`);

  // Phase D's own pair, in the same catalog: trained on its one road, so the caveat stays.
  h.change(nodes['pick-experiment'], 'runs');
  h.change(nodes['pick-pair'], '0');
  const phaseD = byClass(nodes['pick-note'], 'blind');
  assert.ok(phaseD[0].textContent.includes(AR('agents.car.blind_phase_d')), 'Phase D keeps its caveat');
  const was = lanes(nodes['verdict-scored']);
  assert.ok(was.every(li => !li.textContent.includes('أُعيد بناؤها')), 'a certificate written at training is not called reconstructed');

  h.change(nodes['pick-experiment'], 'runs_terrain_dt1');
  h.change(nodes['pick-pair'], '0');
  h.change(nodes['pick-episode'], '1');
  assert.equal(nodes.compute.disabled, false);
});

// Starts from: runs_terrain_dt1, seed 0, episode 1, nothing computed.
test('the device line names the device the scores were reproduced on, and warns only on another', async () => {
  nodes.compute.click();
  const first = await h.nextRequest();
  assert.equal(new URL(first.url, 'http://x').pathname, '/api/agents/episode');
  const versions = { torch: '2.14.0+cpu', sb3: '2.9.0' };
  h.reply(first, { status: 'building', since: 0, steps: 719, frames: [{ k: 0, cars: [car(), car()] }],
    meta: META, road: ROAD, device: 'cpu', versions });
  await h.settle();
  const line = nodes['device-line'];
  assert.match(line.textContent, /أُعيد إنتاج النتائج المحفوظة على/, 'the line says where the committed scores were reproduced');
  assert.ok(line.textContent.includes('cpu'));
  assert.ok(!line.textContent.includes('cuda'), `nothing about cuda is known of these agents: ${line.textContent}`);
  assert.equal(byClass(line, 'device-warning').length, 0, 'computed on the device that reproduced the scores: no warning');
  // The blind car's inputs are zeros, and the memorisation caveat is not said.
  assert.ok(!nodes['seen-blind'].textContent.includes('قد يحفظه'), nodes['seen-blind'].textContent);

  const next = await h.nextRequest();
  h.reply(next, { status: 'ready', since: 1, steps: 719, frames: [], device: 'cuda:0', versions });
  await h.settle();
  const warning = byClass(nodes['device-line'], 'device-warning');
  assert.equal(warning.length, 1, 'computed on another device: said so');
  assert.match(warning[0].textContent, /cpu/, 'the warning names the device the scores were reproduced on');
});

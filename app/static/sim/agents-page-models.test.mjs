// The /agents page's hidden models panel (M3 design 7.7), RUNNING against the
// fake DOM and the fake server of agents-page-harness.mjs. Its own file, not
// agents-page-run.test.mjs: each harness file boots agents.mjs once in its own
// process, and the unlock adds two status requests to the ordered request
// queue that run.test's existing tests do not answer.
//
// The tests run IN ORDER and each says the state it starts from: the page's
// state carries from one to the next, and the unlock cannot be undone within
// one boot (only a reload forgets it). Every model reply below is a fake,
// shaped as app/agent_api.py's four routes answer; nothing reaches a model.
// The natural end of an episode is pinned in model-panel.test.mjs instead:
// the harness stubs requestAnimationFrame, so the loop never runs here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, t } from './i18n.mjs';
import { installFakePage, byClass } from './agents-page-harness.mjs';

const CATALOG = {
  ...JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8')),
  sb3: true,
};
const MODEL_IDS = ['models-panel', 'ask-jev', 'ask-laya',
  'model-jev-name', 'model-jev-status', 'model-jev-reason', 'model-jev-latency', 'model-jev-error',
  'model-jev-rows', 'model-jev-sent-body',
  'model-laya-name', 'model-laya-where', 'model-laya-status', 'model-laya-reason', 'model-laya-latency',
  'model-laya-error', 'model-laya-rows', 'model-laya-sent-body'];
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=1',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'play', 'restart', 'seek',
    'footer-index', 'pause-heading', ...MODEL_IDS],
});
const { nodes, requests, nextRequest, reply, fail, settle, seekTo } = h;
// What agents.html says before any script runs.
nodes['models-panel'].hidden = true;
nodes['ask-jev'].disabled = true;
nodes['ask-laya'].disabled = true;

const AR = key => STRINGS.ar[key];
const AGENT = { budget_line: 'trained 300000 steps of 300000 requested' };
const META = {
  runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, protocol: 'd2', agents: [AGENT, AGENT],
  preview_s: [2, 5, 15, 30],
  act: { lo: [-8, -0.15, -40, 0, 0.3], hi: [4, 0.06, 15, 1, 1], neutral_phys: [0, 0, 0, 1, 1] },
  limits: { turb_c: 849.9 },
};
const ROAD = {
  rise_m: 0, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};
const car = {
  cmd: [0, 0, 0, 1, 1], act: [-1.5, 0, 0, 1, 1], held: [false, false, false, false, false],
  preview_pct: [0, 0, 0, 0], map_kpa: 180, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5,
};
const FRAMES = [0, 1, 2].map(k => ({ k, cars: [car, car] }));
const READY = { status: 'ready', since: 0, steps: 3, meta: META, road: ROAD, frames: FRAMES };

// model_questions' five questions: the ASCII keys (design C12) and their levels.
const IDS = ['spark_trim', 'lambda_trim', 'boost_ceiling', 'cooling_fan', 'coolant_pump'];
const KEYS = [
  ['retard 8 deg', 'retard 4 deg', 'no change', 'advance 2 deg', 'advance 4 deg'],
  ['richer by 0.15', 'richer by 0.075', 'no change', 'leaner by 0.03', 'leaner by 0.06'],
  ['ceiling -40 kPa', 'ceiling -20 kPa', 'no change', 'ceiling +7.5 kPa', 'ceiling +15 kPa'],
  ['fan 0 %', 'fan 25 %', 'fan 50 %', 'fan 75 %', 'fan 100 %'],
  ['pump 30 %', 'pump 47.5 %', 'pump 65 %', 'pump 82.5 %', 'pump 100 %'],
];
const LEVELS = [[-8, -4, 0, 2, 4], [-0.15, -0.075, 0, 0.03, 0.06], [-40, -20, 0, 7.5, 15],
  [0, 0.25, 0.5, 0.75, 1], [0.3, 0.475, 0.65, 0.825, 1]];
// One action as to_action returns it: option j of action i chosen.
const pick = (i, j) => ({
  choice: KEYS[i][j],
  level_phys: LEVELS[i][j],
  level_net: 2 * (LEVELS[i][j] - LEVELS[i][0]) / (LEVELS[i][4] - LEVELS[i][0]) - 1,
  probabilities: Object.fromEntries(KEYS[i].map((key, n) => [key, n === j ? 0.6 : 0.1])),
  chosen_p: 0.6,
  options: KEYS[i].map((key, n) => ({ key, level_phys: LEVELS[i][n] })),
});
const ANSWERS = Object.fromEntries(IDS.map((id, i) => [id, pick(i, 2)]));
// With the options reversed, spark moves and the other four hold.
const REVERSED = { ...ANSWERS, spark_trim: pick(0, 4) };
const LAYA_OK = {
  model: 'laya', runs_on: 'local', model_name: 'laya-rl-agent', laya: '0.3.20', device: 'cuda', ms: 70.2,
  started_s: 6.1, answers: ANSWERS, answers_reversed: REVERSED,
  usage: [{ input_tokens: 2729, output_tokens: 0 }, { input_tokens: 2729, output_tokens: 0 }],
  sent: [{ state: {}, questions: {} }, { state: {}, questions: {} }], trace: 'runs_c4/5/1', step: 0,
};
const LAYA_READY = { configured: true, source: 'env', problem: null, worker: 'ready', device: 'cuda', laya: '0.3.20' };
const rowsOf = name => byClass(nodes[`model-${name}-rows`], 'model-row');

await import('./agents.mjs');
reply(await nextRequest(), CATALOG);
await settle();

// Starts from: runs_c4 / 5 / 1 selected, nothing computed, locked.
test('locked, nothing is asked and no model node is touched, even with a finished episode on screen', async () => {
  nodes.compute.click();
  reply(await nextRequest(), READY);
  await settle();
  nodes.play.click();
  nodes.play.click();
  await settle();
  assert.equal(requests.length, 0, 'a model or status request before the gesture');
  assert.equal(nodes['models-panel'].hidden, true);
  for (const id of MODEL_IDS) assert.equal(nodes[id].textContent, '', `#${id} was written while locked`);
  assert.equal(nodes['ask-jev'].disabled, true);
  assert.equal(nodes['ask-laya'].disabled, true);
});

// Starts from: a finished episode at second 0, never played past it; locked.
test('nine taps unlock nothing; the tenth shows the panel and asks for both statuses, each on its own', async () => {
  for (let i = 0; i < 9; i++) nodes['footer-index'].click();
  assert.equal(nodes['models-panel'].hidden, true, 'nine taps unlock nothing');
  assert.equal(requests.length, 0);
  nodes['footer-index'].click();
  assert.equal(nodes['models-panel'].hidden, false, 'the tenth tap shows the panel');
  const jevStatus = await nextRequest();
  const layaStatus = await nextRequest();
  assert.deepEqual([jevStatus.url, layaStatus.url], ['/api/agents/jev/status', '/api/agents/laya/status']);
  fail(jevStatus);
  reply(layaStatus, { configured: true, source: 'env', problem: null, worker: 'stopped', device: null, laya: null });
  await settle();
  assert.match(nodes['model-jev-status'].textContent, new RegExp(AR('agents.load.server_down')), 'jev\'s failed status stays in jev\'s column');
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.stopped'));
  // A finished episode never played: second 0 can be asked about at once.
  assert.equal(nodes['ask-jev'].disabled, false);
  assert.equal(nodes['ask-laya'].disabled, false);
  assert.equal(nodes['model-laya-reason'].textContent, AR('agents.models.ask_this'));
  for (let i = 0; i < 10; i++) nodes['footer-index'].click();
  await settle();
  assert.equal(requests.length, 0, 'more taps ask nothing more');
});

// Starts from: unlocked, second 0, nothing asked.
test('on a finished episode, play then pause at the same second enables both buttons, with no seek', async () => {
  nodes.play.click();
  assert.equal(nodes['ask-jev'].disabled, true, 'playing');
  assert.equal(nodes['ask-laya'].disabled, true, 'playing');
  assert.equal(nodes['model-jev-reason'].textContent, AR('agents.models.reason.pause'));
  nodes.play.click();
  assert.equal(nodes['ask-jev'].disabled, false, 'paused at the same second');
  assert.equal(nodes['ask-laya'].disabled, false, 'paused at the same second');
  await settle();
  assert.equal(requests.length, 0, 'nothing is asked on its own');
});

// Starts from: unlocked, paused at second 0, nothing asked.
test('a jev failure stays in jev\'s column and Laya still answers, with its order check', async () => {
  nodes['ask-jev'].click();
  const j = await nextRequest();
  assert.equal(j.url, '/api/agents/jev');
  assert.equal(j.init.method, 'POST');
  assert.equal(j.init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(j.init.body), { trace: 'runs_c4/5/1', step: 0 });
  assert.equal(nodes['ask-jev'].disabled, true, 'jev in flight');
  assert.equal(nodes['model-jev-reason'].textContent, AR('agents.models.reason.asking'));
  assert.equal(nodes['ask-laya'].disabled, false, 'jev in flight leaves Laya enabled');
  reply(j, { model: 'jev', code: 'no_key' }, 503);
  await settle();
  assert.equal(nodes['model-jev-error'].hidden, false);
  assert.match(nodes['model-jev-error'].textContent, /no_key/);
  assert.equal(nodes['model-laya-error'].hidden, true, 'nothing reached Laya\'s column');
  assert.equal(nodes['ask-jev'].disabled, false, 'jev can be asked again');

  nodes['ask-laya'].click();
  const l = await nextRequest();
  assert.equal(l.url, '/api/agents/laya');
  assert.deepEqual(JSON.parse(l.init.body), { trace: 'runs_c4/5/1', step: 0 });
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.starting'), 'the first press loads Laya');
  reply(l, LAYA_OK);
  const s = await nextRequest();
  assert.equal(s.url, '/api/agents/laya/status', 'the Laya status is read again after its answer');
  // Before that re-fetch answers, the answer itself already says Laya is loaded.
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.ready').replace('{device}', 'cuda'),
    'the status line waits for the re-fetch beside an answer the loaded worker gave');
  reply(s, LAYA_READY);
  await settle();
  assert.equal(nodes['model-laya-error'].hidden, true);
  assert.equal(nodes['model-jev-error'].hidden, false, 'jev keeps its own error');
  const rows = rowsOf('laya');
  assert.equal(rows.length, 5, 'one row per action');
  assert.equal(byClass(rows[0], 'changed').length, 1, 'spark changed with the order');
  for (const row of rows.slice(1)) assert.equal(byClass(row, 'held').length, 1, 'the other four held');
  assert.equal(byClass(rows[0], 'model-bar').length, 5, 'five bars, one per level');
  assert.equal(byClass(rows[0], 'chosen').length, 1, 'exactly one of them chosen');
  assert.equal(rowsOf('jev').length, 0, 'no rows in jev\'s column');
  assert.match(nodes['model-laya-latency'].textContent, /70 ms/);
  assert.match(nodes['model-laya-latency'].textContent, /6\.1/, 'the first-load seconds');
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.ready').replace('{device}', 'cuda'));
  assert.match(nodes['model-laya-name'].textContent, /laya-rl-agent/);
});

// Starts from: second 0 answered by Laya, jev's no_key at second 0.
test('pausing back at an asked second shows its answer, with no new request', async () => {
  seekTo(2.5);
  assert.equal(rowsOf('laya').length, 0, 'second 2 was never asked');
  assert.equal(nodes['model-laya-reason'].textContent, AR('agents.models.ask_this'));
  assert.equal(nodes['model-jev-error'].hidden, true, 'jev\'s error belongs to second 0');
  seekTo(0.5);
  assert.equal(rowsOf('laya').length, 5, 'second 0\'s answer is shown again');
  assert.equal(nodes['model-jev-error'].hidden, false);
  await settle();
  assert.equal(requests.length, 0, 'no new request');
});

// Starts from: second 0, both columns holding an entry.
test('an answer that arrives after «احسب» belongs to nobody', async () => {
  nodes['ask-laya'].click();
  const late = await nextRequest();
  assert.equal(late.url, '/api/agents/laya');
  nodes.compute.click();
  const episode = await nextRequest();
  assert.match(episode.url, /^\/api\/agents\/episode\?/);
  assert.equal(rowsOf('laya').length, 0, '«احسب» empties both columns');
  assert.equal(nodes['model-jev-error'].hidden, true);
  reply(late, LAYA_OK);
  const status = await nextRequest();
  assert.equal(status.url, '/api/agents/laya/status');
  reply(status, LAYA_READY);
  await settle();
  assert.equal(rowsOf('laya').length, 0, 'the old episode\'s answer was dropped');
  assert.equal(nodes['ask-laya'].disabled, true, 'the new episode is not finished yet');
  reply(episode, READY);
  await settle();
  assert.equal(nodes['ask-laya'].disabled, false, 'free again once the new episode is finished');
  assert.equal(rowsOf('laya').length, 0, 'nothing carried over to the new episode');
});

// Starts from: the new episode, finished, at second 0, nothing asked in it;
// Laya's worker ready. The two columns never meet, in either direction: jev
// failing for want of credit, of a network or of the server leaves Laya's
// answer, button and status as they were, and a Laya failure (with a kind the
// page was not built to show) leaves jev's answer as it was.
test('and the reverse: jev\'s failures never clear Laya\'s answer, and a Laya failure stays in Laya\'s column', async () => {
  const JEV_OK = {
    model: 'jev', runs_on: 'external', model_name: 'jev-latest', ms: 412.3, answers: ANSWERS,
    sent: { model: 'jev-latest', state: {}, questions: {} }, trace: 'runs_c4/5/1', step: 0,
  };
  nodes['ask-laya'].click();
  reply(await nextRequest(), LAYA_OK);
  reply(await nextRequest(), LAYA_READY);
  await settle();
  assert.equal(rowsOf('laya').length, 5);
  const layaStatus = nodes['model-laya-status'].textContent;
  for (const [body, status, shown] of [
    [{ model: 'jev', code: 'vendor_status', status: 402 }, 502, /vendor_status: .*402/],
    [{ model: 'jev', code: 'network' }, 502, /network: /],
    [null, null, new RegExp(AR('agents.load.server_down'))],
  ]) {
    nodes['ask-jev'].click();
    const j = await nextRequest();
    assert.equal(j.url, '/api/agents/jev');
    if (status === null) fail(j); else reply(j, body, status);
    await settle();
    assert.equal(nodes['model-jev-error'].hidden, false);
    assert.match(nodes['model-jev-error'].textContent, shown);
    assert.equal(rowsOf('laya').length, 5, 'Laya\'s answer stays');
    assert.equal(nodes['model-laya-error'].hidden, true, 'nothing reached Laya\'s column');
    assert.equal(nodes['ask-laya'].disabled, false, 'Laya stays askable');
    assert.equal(nodes['model-laya-status'].textContent, layaStatus, 'Laya\'s status line is its own');
    assert.equal(requests.length, 0, 'a jev press reads no Laya status');
  }

  nodes['ask-jev'].click();
  reply(await nextRequest(), JEV_OK);
  await settle();
  assert.equal(nodes['model-jev-error'].hidden, true, 'the new answer replaced jev\'s error at this second');
  assert.equal(rowsOf('jev').length, 5);
  assert.equal(byClass(nodes['model-jev-rows'], 'held').length + byClass(nodes['model-jev-rows'], 'changed').length, 0,
    'jev is asked once: no order check');
  nodes['ask-laya'].click();
  const l = await nextRequest();
  assert.equal(l.url, '/api/agents/laya');
  assert.equal(nodes['ask-jev'].disabled, false, 'Laya in flight leaves jev enabled');
  reply(l, { model: 'laya', code: 'worker_error', kind: 'OSError: C:/Users/admin/secret' }, 502);
  const s = await nextRequest();
  assert.equal(s.url, '/api/agents/laya/status');
  fail(s);
  await settle();
  assert.equal(nodes['model-laya-error'].hidden, false);
  assert.match(nodes['model-laya-error'].textContent, /worker_error: .*\(other\)/);
  assert.doesNotMatch(nodes['model-laya-error'].textContent, /OSError|secret/, 'the server\'s kind text is not shown');
  assert.equal(rowsOf('laya').length, 0, 'the new press at this second replaced Laya\'s answer');
  assert.match(nodes['model-laya-status'].textContent, new RegExp(AR('agents.load.server_down')),
    'Laya\'s failed status request stays in Laya\'s column');
  assert.equal(rowsOf('jev').length, 5, 'jev\'s answer stays');
  assert.equal(nodes['model-jev-error'].hidden, true, 'nothing reached jev\'s column');
  assert.equal(nodes['ask-jev'].disabled, false, 'jev stays askable');
  assert.match(nodes['model-jev-latency'].textContent, /412 ms/);
  assert.match(nodes['model-jev-name'].textContent, /jev-latest/);
});

// U+2066 LEFT-TO-RIGHT ISOLATE, U+2069 POP DIRECTIONAL ISOLATE and U+2212
// MINUS SIGN, built from their code points: each is invisible, or looks like
// an ASCII character, in an editor.
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const MINUS = String.fromCodePoint(0x2212);
const iso = text => `${LRI}${text}${PDI}`;
// Every isolated run, so what is left of a line can be checked for bare digits.
const ISOLATED = new RegExp(`${LRI}[^${PDI}]*${PDI}`, 'g');

// In an Arabic line a bare "+4.0" is drawn "4.0+", and minus 0.075 with its
// sign on the right: the digits after Arabic letters become Arabic numbers
// (UAX #9 W2) and the sign then resolves right-to-left. Measured in the
// browser on 28 Sep (the M3 final review, Important 1), beside bars in a
// left-to-right box that draw the same level with its sign on the left. M2's
// formatDiff isolates the pair row's number; the models panel's choice and
// reversed lines now do the same, and every negative is U+2212, the levels'
// minus, never a hyphen-minus.
// Starts from: the new episode at second 0, jev's answer held there, Laya's
// last press a worker_error.
test('the model lines keep each signed number in a left-to-right isolate, with one minus sign', async () => {
  const signed = {
    ...ANSWERS,
    spark_trim: pick(0, 0),
    lambda_trim: pick(1, 1),
    boost_ceiling: pick(2, 3),
    // NET is float32 (app/model_questions.py): the pump's middle option is
    // -5.96e-08 there, which rounds to zero and reads with no sign.
    coolant_pump: { ...pick(4, 2), level_net: -5.960464477539063e-08 },
  };
  nodes['ask-laya'].click();
  reply(await nextRequest(), { ...LAYA_OK, answers: signed, answers_reversed: { ...signed, spark_trim: pick(0, 4) } });
  reply(await nextRequest(), LAYA_READY);
  await settle();
  const rows = rowsOf('laya');
  assert.equal(rows.length, 5);
  const choice = i => byClass(rows[i], 'model-choice')[0].textContent;
  const reversed = i => byClass(rows[i], 'model-order')[0].children[0].textContent;
  const expect = (level, net) => t('ar', 'agents.models.choice', { level: iso(level), net: iso(net) });
  assert.equal(choice(0), expect(`${MINUS}8.0`, `${MINUS}1.000`), 'spark: level and network value isolated, U+2212');
  assert.equal(choice(1), expect(`${MINUS}0.075`, `${MINUS}0.286`), 'lambda: level and network value isolated, U+2212');
  assert.equal(choice(2), expect('+7.5', '0.727'), 'boost: a positive level keeps its plus, inside the isolate');
  assert.equal(choice(4), expect('0.65', '0.000'), 'pump: a float32 zero reads 0.000, with no sign');
  assert.equal(reversed(0), t('ar', 'agents.models.reversed', { level: iso('+4.0') }), 'spark reversed: +4.0, isolated');
  assert.equal(reversed(1), t('ar', 'agents.models.reversed', { level: iso(`${MINUS}0.075`) }), 'lambda reversed: U+2212, isolated');
  for (const [i, row] of rows.entries()) {
    for (const line of [choice(i), reversed(i)]) {
      assert.doesNotMatch(line, /-/, `row ${i}: a hyphen-minus in "${line}"`);
      assert.doesNotMatch(line.replace(ISOLATED, ''), /\d/, `row ${i}: a number outside an isolate in "${line}"`);
    }
    assert.equal(byClass(row, 'model-choice').length, 1);
  }
});

// «{ms} ms على {device}» was drawn "cuda على ms 65" (measured 28 Sep), and the
// vendor's "70–500 ms" after Arabic letters is predicted to draw "ms 500–70".
// Each Latin run that must keep its order is its own left-to-right isolate in
// the Arabic strings (agents-strings.mjs), as the refused labels isolate a name.
// Starts from: second 0 holding jev's answer (412.3 ms) and Laya's (70.2 ms on cuda).
test('both latency lines keep their Latin runs in order, each in a left-to-right isolate', () => {
  const laya = nodes['model-laya-latency'].textContent;
  assert.ok(laya.startsWith(`${iso('70 ms')} على ${iso('cuda')}`), `Laya's latency line: "${laya}"`);
  const jev = nodes['model-jev-latency'].textContent;
  assert.ok(jev.startsWith(iso('412 ms')), `jev's measured latency is not isolated: "${jev}"`);
  assert.ok(jev.includes(`(ادعاء المورّد ${iso('70–500 ms')})`), `jev's vendor range is not isolated: "${jev}"`);
});

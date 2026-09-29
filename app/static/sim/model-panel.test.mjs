// The models panel's pure logic (M3 design 7.5b, 7.7 and 7.9): when each
// model's button may be pressed, which answer each second keeps, how an
// answer becomes five rows with the order check, and what an error says.
// agents.mjs only wires these to the page, so every decision is pinned here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import { ACTIONS } from './agent-view.mjs';
import {
  MODELS, QUESTION_IDS, ERROR_CODES, askState, createAnswers, rowView, failureOf, errorText, statusLine,
  keyErrorText,
} from './model-panel.mjs';

const SRC = readFileSync(new URL('./model-panel.mjs', import.meta.url), 'utf8');
const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const UNFILLED = /[{][a-z0-9_]+[}]/i;

// Frames as the episode route serves them: { k, cars: [sighted, blind] }.
const frames = n => Array.from({ length: n }, (_, k) => ({ k, cars: [{ k }, { k }] }));
// A finished 719-step episode, stopped (the play button shows play), nothing in flight.
const FULL = frames(719);
const view = over => ({ playing: false, waiting: false, done: true, frames: FULL, inFlight: false, ...over });
// The sighted lane (cars[0]) goes null from step `at` on, as agents.mjs carOf reads it.
function sightedStopsAt(n, at) {
  const f = frames(n);
  for (let k = at; k < n; k++) f[k].cars[0] = null;
  return f;
}

// The shape app/model_questions.py to_action returns for one question
// (Task 2), with the keys and levels of design section 7: five options in the
// design's order, each with its physical level, and five probabilities.
const KEYS = {
  spark_trim: ['retard 8 deg', 'retard 4 deg', 'no change', 'advance 2 deg', 'advance 4 deg'],
  lambda_trim: ['richer by 0.15', 'richer by 0.075', 'no change', 'leaner by 0.03', 'leaner by 0.06'],
  boost_ceiling: ['ceiling -40 kPa', 'ceiling -20 kPa', 'no change', 'ceiling +7.5 kPa', 'ceiling +15 kPa'],
  cooling_fan: ['fan 0 %', 'fan 25 %', 'fan 50 %', 'fan 75 %', 'fan 100 %'],
  coolant_pump: ['pump 30 %', 'pump 47.5 %', 'pump 65 %', 'pump 82.5 %', 'pump 100 %'],
};
const LEVELS = {
  spark_trim: [-8, -4, 0, 2, 4],
  lambda_trim: [-0.15, -0.075, 0, 0.03, 0.06],
  boost_ceiling: [-40, -20, 0, 7.5, 15],
  cooling_fan: [0, 0.25, 0.5, 0.75, 1],
  coolant_pump: [0.3, 0.475, 0.65, 0.825, 1],
};
const LO = [-8, -0.15, -40, 0, 0.3];
const HI = [4, 0.06, 15, 1, 1];
const P = [0.05, 0.6, 0.2, 0.1, 0.05];
function actionOf(id, j) {
  const i = QUESTION_IDS.indexOf(id);
  const key = KEYS[id][j];
  const level = LEVELS[id][j];
  return {
    choice: key,
    level_phys: level,
    level_net: 2 * (level - LO[i]) / (HI[i] - LO[i]) - 1,
    probabilities: Object.fromEntries(KEYS[id].map((k, m) => [k, P[m]])),
    chosen_p: P[j],
    options: KEYS[id].map((k, m) => ({ key: k, level_phys: LEVELS[id][m] })),
  };
}
// choices: the option index each question picked, in QUESTION_IDS order.
const answersOf = choices => Object.fromEntries(QUESTION_IDS.map((id, i) => [id, actionOf(id, choices[i])]));

test('five questions, one per action, in ACTIONS order; two models', () => {
  assert.deepEqual([...MODELS], ['jev', 'laya']);
  assert.equal(QUESTION_IDS.length, 5);
  assert.equal(ACTIONS.length, 5);
  assert.deepEqual(ACTIONS.map((a, i) => [a.key, QUESTION_IDS[i]]), [
    ['spark', 'spark_trim'], ['lambda', 'lambda_trim'], ['boost', 'boost_ceiling'],
    ['fan', 'cooling_fan'], ['pump', 'coolant_pump'],
  ]);
});

test('askState: a finished, stopped episode can be asked about, and each condition alone disables it', () => {
  assert.deepEqual(askState(view({}), 312), { enabled: true, reason: null });
  assert.deepEqual(askState(view({ playing: true }), 312), { enabled: false, reason: 'agents.models.reason.pause' });
  assert.deepEqual(askState(view({ waiting: true }), 312), { enabled: false, reason: 'agents.models.reason.pause' });
  assert.deepEqual(askState(view({ done: false }), 312), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({ inFlight: true }), 312), { enabled: false, reason: 'agents.models.reason.asking' });
  // The sighted lane stopped AT k, or before it: frame k has no sighted car.
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 312) }), 312),
    { enabled: false, reason: 'agents.models.reason.stopped' });
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 311) }), 312),
    { enabled: false, reason: 'agents.models.reason.stopped' });
  // Stopped one step AFTER k: frame k still has its sighted car.
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 313) }), 312), { enabled: true, reason: null });
});

test('askState: the natural end and a never-played episode are enabled with no seek', () => {
  // Played to its end: the clock stops by itself, userPaused stays false
  // (agent-view.mjs:185), and the play button shows play (design C10).
  assert.deepEqual(askState(view({}), 718), { enabled: true, reason: null });
  // Finished and never played: the clock sits at second 0.
  assert.deepEqual(askState(view({}), 0), { enabled: true, reason: null });
});

test('askState: before any episode the reason says what to do; a second outside the episode is refused', () => {
  // state after load and after compute(): no frames, not done, lastK -2.
  assert.deepEqual(askState({ playing: false, waiting: false, done: false, frames: [], inFlight: false }, -2),
    { enabled: false, reason: 'agents.pause.empty' });
  assert.deepEqual(askState(view({}), -2), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({}), 719), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({}), 1.5), { enabled: false, reason: 'agents.models.reason.not_done' });
});

test('askState: one model in flight leaves the other enabled', () => {
  const jev = view({ inFlight: true });
  const laya = view({ inFlight: false });
  assert.equal(askState(jev, 312).enabled, false);
  assert.equal(askState(laya, 312).enabled, true);
});

test('every reason askState gives is a string in both languages', () => {
  const reasons = ['agents.pause.empty', 'agents.models.reason.asking', 'agents.models.reason.not_done',
    'agents.models.reason.pause', 'agents.models.reason.stopped'];
  assert.deepEqual(reasons.filter(k => !has(k)), []);
});

test('createAnswers keeps one answer per (episode, second), in memory, until cleared', () => {
  const answers = createAnswers();
  assert.equal(answers.size, 0);
  answers.put('runs_c4/5/1', 3, { body: 'a' });
  answers.put('runs_c4/5/1', 4, { body: 'b' });
  assert.deepEqual(answers.get('runs_c4/5/1', 3), { body: 'a' }, 'the answer at k1 survives one at k2');
  assert.deepEqual(answers.get('runs_c4/5/1', 4), { body: 'b' });
  assert.equal(answers.get('runs_c4/5/2', 3), null, 'another episode at the same second has no answer');
  assert.equal(answers.get('runs_c4/5/1', 5), null);
  answers.put('runs_c4/5/1', 3, { failure: { code: 'busy', status: null, kind: null } });
  assert.deepEqual(answers.get('runs_c4/5/1', 3), { failure: { code: 'busy', status: null, kind: null } },
    'a second press at the same second replaces the first');
  assert.equal(answers.size, 2);
  answers.clear();
  assert.equal(answers.size, 0);
  assert.equal(answers.get('runs_c4/5/1', 4), null);
});

test('rowView: the choice, five bars in the options order, and the order check', () => {
  // Laya: spark changed with the order (1 -> 3); lambda held (1 -> 1).
  const body = { answers: answersOf([1, 1, 2, 4, 0]), answers_reversed: answersOf([3, 1, 2, 4, 0]) };
  const spark = rowView(body, 0);
  assert.equal(spark.id, 'spark_trim');
  assert.equal(spark.choice, 'retard 4 deg');
  assert.equal(spark.level, -4);
  assert.equal(spark.net, 2 * (-4 + 8) / 12 - 1);
  assert.equal(spark.chosenP, 0.6);
  assert.deepEqual(spark.bars.map(b => b.key), KEYS.spark_trim);
  assert.deepEqual(spark.bars.map(b => b.level), LEVELS.spark_trim);
  assert.deepEqual(spark.bars.map(b => b.p), P);
  assert.deepEqual(spark.bars.map(b => b.chosen), [false, true, false, false, false]);
  assert.deepEqual(spark.reversed, { choice: 'advance 2 deg', level: 2 });
  assert.equal(spark.verdict, 'changed');
  const lambda = rowView(body, 1);
  assert.equal(lambda.id, 'lambda_trim');
  assert.deepEqual(lambda.reversed, { choice: 'richer by 0.075', level: -0.075 });
  assert.equal(lambda.verdict, 'held');
  assert.deepEqual(QUESTION_IDS.map((_, i) => rowView(body, i).verdict), ['changed', 'held', 'held', 'held', 'held']);
});

test('rowView: jev has no order check; a missing action gives no row', () => {
  const jev = rowView({ answers: answersOf([2, 2, 2, 2, 2]) }, 4);
  assert.equal(jev.id, 'coolant_pump');
  assert.equal(jev.choice, 'pump 65 %');
  assert.equal(jev.reversed, null);
  assert.equal(jev.verdict, null);
  assert.equal(jev.bars.filter(b => b.chosen).length, 1);
  const partial = answersOf([2, 2, 2, 2, 2]);
  delete partial.boost_ceiling;
  assert.equal(rowView({ answers: partial }, 2), null);
  assert.equal(rowView({ answers: { spark_trim: { choice: 'no change' } } }, 0), null, 'no options, no bars');
  assert.equal(rowView(null, 0), null);
  assert.equal(rowView({ answers: answersOf([2, 2, 2, 2, 2]) }, 5), null);
});

test('every error code has its sentence in both languages', () => {
  // 21 from M3, and bad_key and bad_key_request from the jev key field (29 Sep).
  assert.equal(ERROR_CODES.length, 23);
  assert.equal(new Set(ERROR_CODES).size, 23);
  assert.ok(ERROR_CODES.includes('bad_key') && ERROR_CODES.includes('bad_key_request'));
  assert.deepEqual(ERROR_CODES.filter(code => !has(`agents.models.error.${code}`)), []);
  assert.ok(has('agents.models.error.server_error'));
});

test('failureOf: a known code keeps only its code, integer status and kind; anything else is a server error', () => {
  assert.deepEqual(failureOf(502, { model: 'jev', code: 'vendor_status', status: 402 }),
    { code: 'vendor_status', status: 402, kind: null });
  assert.deepEqual(failureOf(502, { model: 'laya', code: 'worker_error', kind: 'ValueError' }),
    { code: 'worker_error', status: null, kind: 'ValueError' });
  assert.deepEqual(failureOf(503, { model: 'jev', code: 'no_key' }), { code: 'no_key', status: null, kind: null });
  assert.deepEqual(failureOf(502, { code: 'vendor_status', status: '402' }), { code: 'vendor_status', status: null, kind: null });
  assert.deepEqual(failureOf(500, { detail: 'Internal Server Error' }), { code: 'server_error', status: 500, kind: null });
  assert.deepEqual(failureOf(422, { detail: [{ loc: ['body', 'step'] }] }), { code: 'server_error', status: 422, kind: null });
  assert.deepEqual(failureOf(502, { code: 'made_up' }), { code: 'server_error', status: 502, kind: null });
  // The server's own 500 (agent_api's server_error) is not a model's code: HTTP 500.
  assert.deepEqual(failureOf(500, { model: 'laya', code: 'server_error' }), { code: 'server_error', status: 500, kind: null });
  assert.deepEqual(failureOf(502, null), { code: 'server_error', status: 502, kind: null });
  assert.deepEqual(failureOf(null, null), { code: 'server_down', status: null, kind: null });
  assert.deepEqual(failureOf(undefined, undefined), { code: 'server_down', status: null, kind: null });
});

// The server already maps any other worker kind to 'other' (app/laya_bridge.py
// KINDS); the page does not rest on that. Whatever string arrives as `kind`,
// only the four names the server can send are ever shown.
test('failureOf: a kind is one of the four names the server can send, and any other string is other', () => {
  for (const kind of ['ValueError', 'RuntimeError', 'OutOfMemoryError', 'other']) {
    assert.equal(failureOf(502, { model: 'laya', code: 'worker_error', kind }).kind, kind);
  }
  for (const kind of ['OSError', 'valueerror', 'ValueError: bad', 'Traceback (most recent call last)',
    'C:/Users/admin/secret', '', 'toString', '__proto__', 'constructor']) {
    assert.equal(failureOf(502, { model: 'laya', code: 'worker_error', kind }).kind, 'other', JSON.stringify(kind));
  }
  for (const kind of [42, true, ['ValueError'], { name: 'ValueError' }, null, undefined]) {
    assert.equal(failureOf(502, { model: 'laya', code: 'worker_error', kind }).kind, null, JSON.stringify(kind));
  }
  const odd = failureOf(502, { model: 'laya', code: 'worker_error', kind: 'OSError: C:/Users/admin/secret' });
  for (const lang of LANGS) {
    const text = errorText(odd.code, odd.status, lang, odd.kind);
    assert.match(text, /\(other\)/);
    assert.doesNotMatch(text, /OSError|secret/);
  }
});

test('errorText: «لا جواب — code: sentence», credit named on vendor_status, nothing substituted', () => {
  const credit = failureOf(502, { model: 'jev', code: 'vendor_status', status: 402 });
  assert.equal(errorText(credit.code, credit.status, 'ar', credit.kind),
    'لا جواب — vendor_status: رفضت الخدمة الطلب (HTTP 402). قد يعني ذلك أن الحساب بلا رصيد.');
  assert.equal(errorText(credit.code, credit.status, 'en', credit.kind),
    'No answer — vendor_status: The service refused the request (HTTP 402). This may mean the account has no credit.');
  assert.equal(errorText('no_key', null, 'ar'), 'لا جواب — no_key: لا مفتاح، فلم يُرسل شيء.');
  assert.match(errorText('worker_error', null, 'en', 'OutOfMemoryError'), /^No answer — worker_error: .*\(OutOfMemoryError\)/);
  assert.match(errorText('worker_error', null, 'en', null), /\(other\)/);
});

test('errorText: an unknown code is a server error with its HTTP status; a failed fetch is the server-down sentence', () => {
  const odd = failureOf(500, { detail: 'x' });
  assert.equal(errorText(odd.code, odd.status, 'ar', odd.kind), 'لا جواب — خطأ في الخادم (HTTP 500)');
  assert.equal(errorText(odd.code, odd.status, 'en', odd.kind), 'No answer — Server error (HTTP 500)');
  const down = failureOf(null, null);
  assert.equal(errorText(down.code, down.status, 'ar', down.kind), `لا جواب — ${STRINGS.ar['agents.load.server_down']}`);
  assert.equal(errorText(down.code, down.status, 'en', down.kind), `No answer — ${STRINGS.en['agents.load.server_down']}`);
});

test('no error text leaves a {placeholder} unfilled, whatever the status and kind', () => {
  for (const lang of LANGS) {
    for (const code of [...ERROR_CODES, 'server_error', 'server_down', 'made_up']) {
      for (const [status, kind] of [[402, 'ValueError'], [null, null]]) {
        const text = errorText(code, status, lang, kind);
        assert.doesNotMatch(text, UNFILLED, `${lang} ${code}: ${text}`);
        assert.ok(!text.includes('agents.'), `${lang} ${code}: a key is showing: ${text}`);
      }
    }
  }
});

test('statusLine: jev says whether a key is configured, never the key', () => {
  assert.equal(statusLine('jev', { configured: false, source: null }, null, false, 'ar'), 'لا مفتاح؛ لن يُرسل شيء');
  assert.equal(statusLine('jev', { configured: false, source: null }, null, false, 'en'), 'No key; nothing will be sent');
  assert.equal(statusLine('jev', null, null, false, 'en'), '—');
});

// The jev key field (29 Sep, after M3): a key pasted on the page says so, and
// the other two sources are words, so no raw token ('env', 'file') shows
// inside an Arabic line; a source the page does not know is a dash.
test('statusLine: jev names where its key comes from, in words, in both languages', () => {
  const on = source => ({ configured: true, source });
  const line = (source, lang) => statusLine('jev', on(source), null, false, lang);
  assert.equal(line('page', 'ar'), 'مفتاح من الصفحة، لهذه الجلسة فقط');
  assert.equal(line('page', 'en'), 'Key from this page, for this session only');
  assert.equal(line('env', 'ar'), 'مفتاح مُعَدّ (من متغيّر البيئة)');
  assert.equal(line('env', 'en'), 'Key configured (from the environment variable)');
  assert.equal(line('file', 'ar'), 'مفتاح مُعَدّ (من ملف)');
  assert.equal(line('file', 'en'), 'Key configured (from a file)');
  assert.equal(line('made_up', 'en'), 'Key configured (—)', 'an unknown source is never shown as sent');
  for (const source of ['page', 'env', 'file', 'made_up', 'toString', null]) {
    assert.doesNotMatch(line(source, 'ar'), /[A-Za-z]/, `ar ${source}: a Latin token inside an Arabic line`);
    for (const lang of LANGS) assert.doesNotMatch(line(source, lang), UNFILLED);
  }
});

test('keyErrorText: the code\'s own sentence for jev\'s key field, nothing substituted', () => {
  const text = (status, body, lang) => keyErrorText(failureOf(status, body), lang);
  assert.equal(text(422, { model: 'jev', code: 'bad_key' }, 'ar'), 'تعذّر استعمال هذا المفتاح؛ لم يُحفظ شيء.');
  assert.equal(text(422, { model: 'jev', code: 'bad_key' }, 'en'), 'This key could not be used; nothing was kept.');
  assert.equal(text(422, { model: 'jev', code: 'bad_key_request' }, 'ar'), 'طلب غير صالح؛ لم يُحفظ شيء.');
  assert.equal(text(422, { model: 'jev', code: 'bad_key_request' }, 'en'), 'Invalid request; nothing was kept.');
  assert.equal(text(403, { model: 'jev', code: 'foreign_origin' }, 'en'), STRINGS.en['agents.models.error.foreign_origin']);
  // The server's own 500 and anything unknown: a server error with its HTTP status.
  assert.equal(text(500, { model: 'jev', code: 'server_error' }, 'en'), 'Server error (HTTP 500)');
  assert.equal(text(422, { detail: [{ input: 'sentinel' }] }, 'en'), 'Server error (HTTP 422)');
  assert.equal(text(null, null, 'ar'), STRINGS.ar['agents.load.server_down']);
  for (const lang of LANGS) {
    for (const code of [...ERROR_CODES, 'server_error', 'server_down', 'made_up']) {
      const t = keyErrorText({ code, status: null, kind: null }, lang);
      assert.doesNotMatch(t, UNFILLED, `${lang} ${code}: ${t}`);
      assert.ok(!t.includes('agents.'), `${lang} ${code}: a key is showing: ${t}`);
    }
  }
});

test('statusLine: Laya reads its worker state, and a failed status request stays in its own column', () => {
  const laya = over => ({ configured: true, source: 'env', problem: null, worker: 'stopped', device: null, laya: null, ...over });
  const line = (status, inFlight = false, lang = 'en') => statusLine('laya', status, null, inFlight, lang);
  assert.equal(line(laya({ configured: false, source: null, problem: 'not_configured' })), 'Not configured: LAYA_HOME');
  assert.equal(line(laya({ problem: 'not_found' })), STRINGS.en['agents.models.laya.status.not_found']);
  assert.equal(line(laya({})), 'Loads on the first question');
  assert.equal(line(laya({}), true), 'Loading on this machine for the first time…');
  assert.equal(line(laya({ worker: 'starting' })), 'Loading on this machine for the first time…');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' })), 'Loaded on cuda until the server stops');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' }), true), 'Loaded on cuda until the server stops');
  assert.equal(line(laya({ worker: 'failed', problem: 'start_timeout' })), 'Could not start: start_timeout');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' }), false, 'ar'), 'محمَّل على cuda حتى يُغلق الخادم');
  // The status request itself failed: the server-down sentence, in this column.
  assert.equal(statusLine('laya', null, failureOf(null, null), false, 'en'), `No answer — ${STRINGS.en['agents.load.server_down']}`);
  for (const lang of LANGS) {
    for (const s of [laya({}), laya({ worker: 'failed', problem: null }), laya({ worker: 'ready', device: null })]) {
      assert.doesNotMatch(statusLine('laya', s, null, false, lang), UNFILLED);
    }
  }
});

test('model-panel.mjs is pure and names only keys that exist', () => {
  assert.doesNotMatch(SRC, /\bfetch\s*\(|\bdocument\.|\bwindow\.|\bglobalThis\b|localStorage|sessionStorage|indexedDB|cookie/);
  // Design C9: the model's own confidence is never read, so it can never be shown.
  assert.doesNotMatch(SRC, /\.confidence\b|\[\s*['"]confidence/);
  const literals = [...new Set([...SRC.matchAll(/'(agents\.[\w.]+)'/g)].map(m => m[1]))];
  assert.ok(literals.length >= 10, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(literals.filter(k => !has(k)), []);
});

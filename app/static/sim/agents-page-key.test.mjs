// The jev key field in the hidden models panel (Jad, 29 Sep, after M3; the
// walkthrough log of docs/superpowers/specs/2026-09-26-agent-replay-design.md):
// the key typed into jev's column goes to the server's memory, the field is
// emptied BEFORE the request leaves, nothing about it is stored in the
// browser, and it is never shown again. RUNNING against the fake DOM and the
// fake server of agents-page-harness.mjs, in its own file because each
// harness file boots agents.mjs once in its own process.
//
// The tests run IN ORDER and each says the state it starts from. Every reply
// below is a fake, shaped as app/agent_api.py answers; nothing reaches a
// server, and the key is a sentinel, not a key.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage } from './agents-page-harness.mjs';

const TYPED = 'sentinel-not-a-real-key-0000';
const CATALOG = {
  ...JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8')),
  sb3: true,
};
const KEY_IDS = ['jev-key', 'jev-key-save', 'jev-key-clear', 'jev-key-error', 'jev-key-note'];
const MODEL_IDS = ['models-panel', 'ask-jev', 'ask-laya', 'model-jev-status', 'model-jev-error',
  'model-laya-status', 'model-laya-error'];
const h = installFakePage({ search: '', ids: ['footer-index', ...MODEL_IDS, ...KEY_IDS] });
const { nodes, requests, nextRequest, reply, fail, settle } = h;
// What agents.html says before any script runs.
nodes['models-panel'].hidden = true;
nodes['jev-key-error'].hidden = true;
nodes['model-jev-error'].hidden = true;
nodes['model-laya-error'].hidden = true;

const AR = key => STRINGS.ar[key];
const WHERE = { vendor: 'typesafe.ai', model: 'jev-latest', hosted: 'USA' };
const NO_KEY = { configured: false, source: null, ...WHERE };
const PAGE_KEY = { configured: true, source: 'page', ...WHERE };
const LAYA = { configured: false, source: null, problem: 'not_configured', worker: 'stopped', device: null, laya: null };

// Every browser store, as a trap that records each touch. agents.mjs reads
// and writes the lab's theme and language through localStorage; nothing else
// may be touched, and nothing touched may hold the key.
const touched = [];
const trapStore = name => ({
  getItem: key => { touched.push([name, 'get', key]); return null; },
  setItem: (key, value) => { touched.push([name, 'set', key, String(value)]); },
  removeItem: key => { touched.push([name, 'remove', key]); },
  clear: () => { touched.push([name, 'clear']); },
  key: () => { touched.push([name, 'key']); return null; },
});
globalThis.localStorage = trapStore('localStorage');
globalThis.sessionStorage = trapStore('sessionStorage');
globalThis.indexedDB = { open: name => { touched.push(['indexedDB', 'open', name]); throw new Error('trap'); } };
Object.defineProperty(globalThis.document, 'cookie', {
  get() { touched.push(['cookie', 'get']); return ''; },
  set(value) { touched.push(['cookie', 'set', String(value)]); },
});

// Every request, with what the field held at the moment fetch was called.
const harnessFetch = globalThis.fetch;
const atSend = [];
globalThis.fetch = (url, init) => {
  atSend.push({ url: String(url), field: nodes['jev-key'].value });
  return harnessFetch(url, init);
};

function allText(node) {
  return [node.textContent, node.value, node.title, ...Object.values(node.attrs || {}),
    ...(node.children || []).map(allText)].join(' ');
}

await import('./agents.mjs');
reply(await nextRequest(), CATALOG);
await settle();
for (let i = 0; i < 10; i++) nodes['footer-index'].click();
const firstJev = await nextRequest();
const firstLaya = await nextRequest();
assert.deepEqual([firstJev.url, firstLaya.url], ['/api/agents/jev/status', '/api/agents/laya/status']);
reply(firstJev, NO_KEY);
reply(firstLaya, LAYA);
await settle();

// Starts from: unlocked, jev with no key, Laya not configured, no episode.
test('an empty field sends nothing, and neither does one holding only spaces', async () => {
  assert.equal(nodes['model-jev-status'].textContent, AR('agents.models.jev.status.no_key'));
  nodes['jev-key'].value = '';
  nodes['jev-key-save'].click();
  nodes['jev-key'].value = '    ';
  nodes['jev-key-save'].click();
  await settle();
  assert.equal(requests.length, 0, 'nothing is sent for an empty field');
  assert.equal(nodes['jev-key'].value, '');
  assert.equal(nodes['jev-key-error'].hidden, true);
});

// Starts from: no key anywhere, nothing in flight.
test('save sends the typed key once, the field already empty when the request leaves, then reads jev\'s status', async () => {
  nodes['jev-key'].value = TYPED;
  nodes['jev-key-save'].click();
  assert.equal(nodes['jev-key'].value, '', 'the field is empty right after the click');
  const r = await nextRequest();
  assert.equal(r.url, '/api/agents/jev/key');
  assert.equal(r.init.method, 'POST');
  assert.equal(r.init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(r.init.body), { key: TYPED });
  assert.deepEqual(atSend.at(-1), { url: '/api/agents/jev/key', field: '' },
    'the field was emptied before fetch was called');
  assert.equal(nodes['jev-key-save'].disabled, true, 'the field\'s buttons wait while the key is in flight');
  assert.equal(nodes['jev-key-clear'].disabled, true);
  nodes['jev-key'].value = 'sentinel-second-press-0000';
  nodes['jev-key-save'].click();
  nodes['jev-key-clear'].click();
  assert.equal(nodes['jev-key'].value, 'sentinel-second-press-0000', 'a press while in flight leaves the field as typed');
  reply(r, PAGE_KEY);
  const s = await nextRequest();
  assert.equal(s.url, '/api/agents/jev/status', 'jev\'s status is read again');
  reply(s, PAGE_KEY);
  await settle();
  assert.equal(requests.length, 0, 'the presses made while in flight sent nothing');
  assert.equal(nodes['model-jev-status'].textContent, 'مفتاح من الصفحة، لهذه الجلسة فقط');
  assert.equal(nodes['jev-key-error'].hidden, true);
  assert.equal(nodes['jev-key-save'].disabled, false);
  assert.equal(nodes['jev-key-clear'].disabled, false);
  nodes['jev-key'].value = '';
});

// Starts from: the page key set, the field empty.
test('clear sends {"key": null}, and the status line says there is no key', async () => {
  nodes['jev-key-clear'].click();
  const r = await nextRequest();
  assert.equal(r.url, '/api/agents/jev/key');
  assert.equal(r.init.method, 'POST');
  assert.equal(r.init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(r.init.body), { key: null });
  reply(r, NO_KEY);
  reply(await nextRequest(), NO_KEY);
  await settle();
  assert.equal(nodes['model-jev-status'].textContent, 'لا مفتاح؛ لن يُرسل شيء');
  assert.equal(nodes['jev-key-error'].hidden, true);
});

// Starts from: no key anywhere. A refused key, a refused request and a server
// that never answered each show in jev's column only, and the next good save
// takes the sentence away.
test('a refused key shows its sentence in jev\'s column only, and a good save takes it away', async () => {
  const layaStatus = nodes['model-laya-status'].textContent;
  for (const [answer, shown] of [
    [{ status: 422, body: { model: 'jev', code: 'bad_key' } }, 'تعذّر استعمال هذا المفتاح؛ لم يُحفظ شيء.'],
    [{ status: 422, body: { model: 'jev', code: 'bad_key_request' } }, 'طلب غير صالح؛ لم يُحفظ شيء.'],
    [{ status: 422, body: { detail: [{ input: TYPED }] } }, AR('agents.models.error.server_error').replace('{status}', '422')],
    [null, AR('agents.load.server_down')],
  ]) {
    nodes['jev-key'].value = 'short';
    nodes['jev-key-save'].click();
    const r = await nextRequest();
    assert.deepEqual(JSON.parse(r.init.body), { key: 'short' });
    if (answer === null) fail(r); else reply(r, answer.body, answer.status);
    reply(await nextRequest(), NO_KEY);
    await settle();
    assert.equal(nodes['jev-key-error'].hidden, false);
    assert.equal(nodes['jev-key-error'].textContent, shown);
    assert.ok(!nodes['jev-key-error'].textContent.includes(TYPED), 'nothing the server echoed is shown');
    assert.equal(nodes['model-jev-error'].hidden, true, 'the ask\'s own error line is untouched');
    assert.equal(nodes['model-laya-error'].hidden, true, 'nothing reached Laya\'s column');
    assert.equal(nodes['model-laya-status'].textContent, layaStatus, 'Laya\'s status line is its own');
    assert.equal(requests.length, 0, 'a key press reads no Laya status');
  }
  nodes['jev-key'].value = TYPED;
  nodes['jev-key-save'].click();
  reply(await nextRequest(), PAGE_KEY);
  reply(await nextRequest(), PAGE_KEY);
  await settle();
  assert.equal(nodes['jev-key-error'].hidden, true, 'a good save takes the sentence away');
  assert.equal(nodes['jev-key-error'].textContent, '');
  assert.equal(nodes['model-jev-status'].textContent, AR('agents.models.jev.status.page'));
});

// Starts from: the page key set. Everything the page drew and everything it
// touched in the browser, read at once.
test('the typed key is never drawn, and nothing about it reaches a browser store', () => {
  for (const [id, node] of Object.entries(nodes)) {
    assert.ok(!allText(node).includes(TYPED), `#${id} holds the typed key`);
  }
  assert.ok(touched.length > 0, 'the trap saw nothing: the lab\'s preferences were not read');
  for (const entry of touched) {
    assert.equal(entry[0], 'localStorage', `touched ${entry.slice(0, 3).join(' ')}`);
    assert.ok(['grad.sim.theme', 'grad.sim.lang'].includes(entry[2]), `touched ${entry.slice(0, 3).join(' ')}`);
    assert.ok(!entry.join(' ').includes('sentinel'), 'a store holds the key');
  }
});

// The same rule, read from the source: the only storage the page uses is the
// lab's two preferences, through remember() and recall().
test('the page source uses no browser storage but the lab\'s two preferences', () => {
  const page = readFileSync(new URL('./agents.mjs', import.meta.url), 'utf8');
  const html = readFileSync(new URL('../agents.html', import.meta.url), 'utf8');
  for (const [name, src] of [['agents.mjs', page], ['agents.html', html]]) {
    assert.doesNotMatch(src, /sessionStorage|indexedDB|IDBFactory|\bcookie|caches\.|CacheStorage|openDatabase/,
      `${name} names a browser store`);
  }
  assert.deepEqual([...page.matchAll(/localStorage\.(\w+)/g)].map(m => m[1]), ['setItem', 'getItem'],
    'agents.mjs uses localStorage only in remember() and recall()');
  const calls = [...page.matchAll(/[^\w]remember\(([^,)]*)/g)].map(m => m[1].trim());
  assert.deepEqual(calls.filter(a => a !== 'key').sort(), ['STORE.lang', 'STORE.theme'],
    'remember() is called only for the theme and the language');
  assert.deepEqual([...html.matchAll(/localStorage\.(\w+)/g)].map(m => m[1]), ['getItem', 'getItem'],
    'agents.html only reads the two preferences before paint');
  const key = page.slice(page.indexOf('function sendJevKey('), page.indexOf('// ---------------------------------------------------------------- per frame'));
  assert.ok(key.length > 100, 'the key code was not found: the scan has drifted');
  assert.doesNotMatch(key, /localStorage|remember\(|console\./, 'the key code stores or logs something');
});

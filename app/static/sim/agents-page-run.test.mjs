// The /agents page RUNNING, against a fake DOM and a fake server: what the
// viewer is actually shown after a failed request is retried, and how a
// grouped number reads in Arabic. agents-page.test.mjs checks the page's text
// without running it; this file runs agents.mjs itself (it exports nothing and
// boots on import), so it owns the globals of its own test process.
//
// The fake DOM holds only the elements these checks read. Every other id is
// null, which agents.mjs already tolerates, so the profile, the chase view and
// the rest of the pause panel stay out of the way.
import test from 'node:test';
import assert from 'node:assert/strict';

class FakeNode {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.own = '';
    this.hidden = false;
    this.disabled = false;
    this.className = '';
    this.dataset = {};
    this.style = {};
    this.attrs = {};
    this.listeners = {};
  }
  get textContent() { return this.own + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.own = String(v); this.children = []; }
  appendChild(node) { this.children.push(node); return node; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return name in this.attrs ? this.attrs[name] : null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  click() { for (const fn of this.listeners.click || []) fn(); }
  querySelector() { return null; }
  querySelectorAll() { return []; }
}

const nodes = Object.fromEntries(['compute', 'error', 'pick-note', 'rise-caption', 'seek', 'actions', 'lane-stopped']
  .map(id => [id, new FakeNode('div')]));
// Every node under `node` whose class list holds `name`.
function byClass(node, name, out = []) {
  if (String(node.className).split(' ').includes(name)) out.push(node);
  for (const child of node.children) byClass(child, name, out);
  return out;
}
globalThis.document = {
  documentElement: new FakeNode('html'),
  activeElement: null,
  getElementById: id => nodes[id] || null,
  createElement: tag => new FakeNode(tag),
  querySelector: () => null,
  querySelectorAll: () => [],
};
globalThis.window = {
  location: { search: '?runs=runs_c4&seed=5&ep=1' },
  matchMedia: () => ({ matches: false }),
};
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
globalThis.requestAnimationFrame = () => 0;

// Each request waits until the test answers it, so the order is the test's.
const requests = [];
let arrived = null;
globalThis.fetch = url => new Promise((resolve, reject) => {
  requests.push({ url: String(url), resolve, reject });
  if (arrived) { arrived(); arrived = null; }
});
async function nextRequest() {
  while (!requests.length) await new Promise(resolve => { arrived = resolve; });
  return requests.shift();
}
const reply = (req, body) => req.resolve({ status: 200, json: async () => body });
const settle = () => new Promise(resolve => setTimeout(resolve, 20));
function seekTo(time) {
  nodes.seek.value = String(time);
  for (const fn of nodes.seek.listeners.input || []) fn();
}

// The page keeps the first meta it is given for a key (applyMeta), so every
// reply here carries this one. act is engine_env's ACT_LO / ACT_HI.
const AGENT = { budget_line: 'trained 300000 steps of 300000 requested' };
const META = {
  runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, protocol: 'd2', agents: [AGENT, AGENT],
  preview_s: [2, 5, 15, 30],
  act: { lo: [-8, -0.15, -40, 0, 0.3], hi: [4, 0.06, 15, 1, 1], neutral_phys: [0, 0, 0, 1, 1] },
};
const ROAD = {
  rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};

await import('./agents.mjs');

const retryButton = () => nodes.error.children.find(c => c.tagName === 'button') || null;

test('a retry that reaches the server clears the "server unavailable" alert', async () => {
  nodes.compute.click();
  const first = await nextRequest();
  assert.match(first.url, /preempt=1/, '«احسب» sends the one preempt=1 request');
  first.reject(new TypeError('Failed to fetch'));
  await settle();
  assert.equal(nodes.error.hidden, false, 'the failure is shown');
  assert.ok(retryButton(), 'with a retry button');

  retryButton().click();
  const second = await nextRequest();
  assert.doesNotMatch(second.url, /preempt=1/, 'a retry waits its turn');
  reply(second, { status: 'building', since: 0, frames: [], steps: 719 });
  const third = await nextRequest();   // the building response was handled
  assert.equal(nodes.error.hidden, true, 'still reads "server unavailable" while building');
  assert.equal(retryButton(), null, 'still offers a retry while building');

  reply(third, { status: 'ready', since: 0, frames: [], steps: 719 });
  await settle();
  assert.equal(nodes.error.hidden, true, 'still reads "server unavailable" after ready');
});

// fmtInt groups thousands. In the Arabic (RTL) page the digits after Arabic
// letters are Arabic numbers (UAX #9 rule W2). A SINGLE separator of bidi
// class CS between two of them joins them into one run (rule W4); a plain
// space (class WS) does not, so each group becomes its own run and the
// right-to-left line swaps them: 300 000 is drawn "000 300". JavaScript has no
// \p{Bidi_Class}, so the CS code points are listed from Unicode's
// DerivedBidiClass.txt; U+00A0 and U+202F are the only spaces among them.
const BIDI_CS = new Set([0x2c, 0x2e, 0x2f, 0x3a, 0xa0, 0x60c, 0x202f, 0x2044,
  0xfe50, 0xfe52, 0xfe55, 0xff0c, 0xff0e, 0xff0f, 0xff1a]);
const cs = ch => BIDI_CS.has(ch.codePointAt(0));
const hex = ch => `U+${ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`;

test('grouped numbers stay in order in Arabic: the thousands separator is bidi class CS', async () => {
  nodes.compute.click();
  const req = await nextRequest();
  reply(req, { status: 'ready', since: 0, frames: [], steps: 719, meta: META, road: ROAD });
  await settle();
  const budget = nodes['pick-note'].textContent.match(/300(\D)000/);
  assert.ok(budget, `no grouped budget in #pick-note: ${nodes['pick-note'].textContent}`);
  assert.ok(cs(budget[1]), `the budget groups are joined by ${hex(budget[1])}, not a CS separator`);
  const rise = nodes['rise-caption'].textContent.match(/2(\D)755/);
  assert.ok(rise, `no grouped rise in #rise-caption: ${nodes['rise-caption'].textContent}`);
  assert.ok(cs(rise[1]), `the rise groups are joined by ${hex(rise[1])}, not a CS separator`);
});

// A lane whose simulation diverged sends one car whose cmd and act are five
// nulls with held all true (agent_trace._car: NaN != NaN, then jsonable), and
// car = null from the next step on. The panel shows a dash for it and never a
// "commanded ...; held back by the rate limit" line, which would have no value.
test('a diverged step and a stopped lane show a dash, never a held command', async () => {
  nodes.compute.click();
  const req = await nextRequest();
  const nulls = [null, null, null, null, null];
  const car = (over = {}) => ({
    cmd: [-1, 0, 0, 0.6, 0.8], act: [-3.5, -0.045, -12.5, 0.8, 0.9],
    held: [false, false, false, false, false], preview_pct: [0, 0, 12, 12],
    map_kpa: 186.6, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5, ...over,
  });
  reply(req, {
    status: 'ready', since: 0, steps: 3, meta: META, road: ROAD,
    frames: [
      { k: 0, cars: [car(), car()] },
      { k: 1, cars: [car({ held: [true, false, false, false, false] }),
        car({ cmd: nulls, act: nulls, held: [true, true, true, true, true], map_kpa: null })] },
      { k: 2, cars: [car(), null] },
    ],
  });
  await settle();
  const rows = () => byClass(nodes.actions, 'action-row');
  const lane = (row, j) => byClass(row, 'car-value')[j];
  const part = (row, j, name) => byClass(lane(row, j), name)[0];
  assert.equal(rows().length, 5, 'five action rows');

  seekTo(1.5);
  const [spark] = rows();
  assert.equal(part(spark, 0, 'held-line').hidden, false, 'the sighted car was held on spark');
  assert.match(part(spark, 0, 'held-line').textContent, /8\.0/, 'with its command, -8.0 degrees');
  rows().forEach((row, i) => {
    assert.equal(part(row, 1, 'value').textContent, '—', `row ${i}: the diverged car's value`);
    assert.equal(part(row, 1, 'held-line').hidden, true, `row ${i}: a held line with no value`);
    assert.equal(byClass(row, 'gauge-dot')[1].hidden, true, `row ${i}: a dot with no value`);
  });

  seekTo(2.5);
  rows().forEach((row, i) => {
    assert.equal(part(row, 1, 'value').textContent, '—', `row ${i}: the stopped car's value`);
    assert.equal(part(row, 1, 'held-line').hidden, true, `row ${i}: the stopped car's held line`);
    assert.equal(part(row, 0, 'held-line').hidden, true, `row ${i}: the sighted car is not held at step 2`);
  });
  assert.equal(nodes['lane-stopped'].hidden, false, 'the stop is said');
  assert.match(nodes['lane-stopped'].textContent, /\b2$/, 'at step 2, the first null car');
});

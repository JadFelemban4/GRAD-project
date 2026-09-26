// The /agents page RUNNING, against a fake DOM and a fake server: what the
// viewer is actually shown after a failed request is retried, and how a
// grouped number reads in Arabic. agents-page.test.mjs checks the page's text
// without running it; this file runs agents.mjs itself (it exports nothing and
// boots on import), so it owns the globals of its own test process.
//
// The fake DOM holds only the elements these checks read. Every other id is
// null, which agents.mjs already tolerates, so the profile, the timeline and
// the pause panel stay out of the way.
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

const nodes = Object.fromEntries(['compute', 'error', 'pick-note', 'rise-caption']
  .map(id => [id, new FakeNode('div')]));
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
  const agent = { budget_line: 'trained 300000 steps of 300000 requested' };
  reply(req, {
    status: 'ready', since: 0, frames: [], steps: 719,
    meta: { runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, agents: [agent, agent] },
    road: {
      rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
      grade_pct: [0, 0], s_m: [0, 1], x_m: [0, 1], z_m: [0, 0],
    },
  });
  await settle();
  const budget = nodes['pick-note'].textContent.match(/300(\D)000/);
  assert.ok(budget, `no grouped budget in #pick-note: ${nodes['pick-note'].textContent}`);
  assert.ok(cs(budget[1]), `the budget groups are joined by ${hex(budget[1])}, not a CS separator`);
  const rise = nodes['rise-caption'].textContent.match(/2(\D)755/);
  assert.ok(rise, `no grouped rise in #rise-caption: ${nodes['rise-caption'].textContent}`);
  assert.ok(cs(rise[1]), `the rise groups are joined by ${hex(rise[1])}, not a CS separator`);
});

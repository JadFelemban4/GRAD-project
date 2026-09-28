// The /agents page RUNNING, against a fake DOM and a fake server
// (agents-page-harness.mjs), opened from a FULL address: what the viewer is
// shown after a failed request is retried, how a grouped number reads in
// Arabic, and the pause panel. agents-page-nav.test.mjs opens the page from
// its nav link instead, agents-page-address.test.mjs from an address that
// names too much; agents-page.test.mjs checks the page's text without running
// it. This file owns the globals of its own test process.
//
// The fake DOM holds only the elements these checks read. Every other id is
// null, which agents.mjs already tolerates, so the profile, the chase view and
// the rest of the pause panel stay out of the way.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { installFakePage, byClass, FakeNode } from './agents-page-harness.mjs';

// The server's own catalog (agent_api.catalog), sb3 pinned true so these tests
// never depend on the machine that generated the fixture.
const CATALOG = {
  ...JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8')),
  sb3: true,
};
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=1',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'rise-caption',
    'seek', 'actions', 'lane-stopped', 'lang-toggle', 'turb-sighted', 'turb-blind'],
});
const { nodes, nextRequest, reply, settle, seekTo } = h;

// The page keeps the first meta it is given for a key (applyMeta), so every
// reply here carries this one. act is engine_env's ACT_LO / ACT_HI.
const AGENT = { budget_line: 'trained 300000 steps of 300000 requested' };
const META = {
  runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, protocol: 'd2', agents: [AGENT, AGENT],
  preview_s: [2, 5, 15, 30],
  act: { lo: [-8, -0.15, -40, 0, 0.3], hi: [4, 0.06, 15, 1, 1], neutral_phys: [0, 0, 0, 1, 1] },
  // agent_api.episode_meta sends round(TURB_PROTECT_K - 273.15, 1)
  limits: { turb_c: 849.9 },
};
const ROAD = {
  rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};

await import('./agents.mjs');
// The page's only request at boot is the catalog; it is answered here, before
// any test, so every test below starts from the restored selection.
const boot = await nextRequest();
reply(boot, CATALOG);
await settle();

const retryButton = () => nodes.error.children.find(c => c.tagName === 'button') || null;

test('a full address restores its selection and computes nothing until «احسب»', async () => {
  assert.equal(boot.url, '/api/agents/catalog');
  assert.equal(nodes['pick-experiment'].value, 'runs_c4');
  assert.equal(nodes['pick-pair'].value, '5');
  assert.equal(nodes['pick-episode'].value, '1');
  assert.equal(nodes.compute.disabled, false, '«احسب» is ready');
  assert.deepEqual(h.history, [], 'an address the catalog allows is kept as it is');
  await settle();
  assert.equal(h.requests.length, 0, 'no episode request before «احسب»');
});

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

// The pause panel's five rows. The three trims have a tick at 0 and its label
// «بلا تعديل» must stand on that tick, at the tick's own left %, in both
// languages: under the end of the bar it read as +4.0 (Arabic) or −8.0
// (English) being "no change". The fan and the pump rows each carry a note
// about their own device (the pump's once described the fan's schedule).
test('«بلا تعديل» sits on the zero tick of each trim row, and the fan and pump notes name their own device', async () => {
  nodes.compute.click();
  reply(await nextRequest(), { status: 'ready', since: 0, frames: [], steps: 719, meta: META, road: ROAD });
  await settle();
  const check = (lang, noChange, own, other) => {
    const rows = byClass(nodes.actions, 'action-row');
    assert.equal(rows.length, 5, `${lang}: five action rows`);
    const ticks = rows.map(row => byClass(row, 'gauge-tick')[0].style.left);
    // gaugeFraction(0, lo, hi): 8/12, 0.15/0.21 and 40/55 of the bar
    assert.deepEqual(ticks.slice(0, 3), ['66.67%', '71.43%', '72.73%'], `${lang}: the zero ticks`);
    rows.slice(0, 3).forEach((row, i) => {
      const labels = byClass(row, 'tick-label');
      assert.equal(labels.length, 1, `${lang} row ${i}: one label at the zero tick`);
      assert.equal(labels[0].textContent, noChange, `${lang} row ${i}: the label's text`);
      assert.equal(labels[0].style.left, ticks[i], `${lang} row ${i}: the label is not at the zero tick`);
      assert.equal(byClass(row, 'tick-note').length, 0, `${lang} row ${i}: a trim row has no paragraph note`);
    });
    rows.slice(3).forEach((row, j) => {
      assert.equal(byClass(row, 'tick-label').length, 0, `${lang} row ${3 + j}: a duty row has no zero label`);
      const note = byClass(row, 'tick-note')[0]?.textContent || '';
      assert.match(note, own[j], `${lang} row ${3 + j}: the note does not name its own device`);
      assert.doesNotMatch(note, other[j], `${lang} row ${3 + j}: the note names the other device`);
    });
  };
  check('ar', 'بلا تعديل', [/المروحة/, /المضخة/], [/المضخة/, /المروحة/]);
  nodes['lang-toggle'].click();
  try {
    check('en', 'No change', [/\bfan\b/, /\bpump\b/], [/\bpump\b/, /\bfan\b/]);
  } finally {
    nodes['lang-toggle'].click();   // back to Arabic for the tests below
  }
});

// The limit is TURB_PROTECT_K - 273.15 = 849.85, sent as 849.9; the results
// files and the documents say 850, so it is shown with no decimals. The
// Arabic readings write degrees Celsius «°م», as the badge and the profile do.
test('the turbine limit reads 850, in °م in Arabic and °C in English', async () => {
  nodes.compute.click();
  const car = { cmd: [0, 0, 0, 1, 1], act: [0, 0, 0, 1, 1], held: [false, false, false, false, false],
    preview_pct: [0, 0, 0, 0], map_kpa: 180, turb_c: 700.4, torque_nm: 300, torque_req_nm: 310, damage: 1.5 };
  reply(await nextRequest(), { status: 'ready', since: 0, steps: 1, meta: META, road: ROAD,
    frames: [{ k: 0, cars: [car, car] }] });
  await settle();
  seekTo(0.5);
  for (const id of ['turb-sighted', 'turb-blind']) {
    assert.equal(nodes[id].textContent, '700 °م / 850 °م', `#${id} in Arabic`);
    assert.equal(nodes[id].dir, 'rtl', `#${id}: an Arabic unit inside a left-to-right box reorders the reading`);
  }
  nodes['lang-toggle'].click();
  try {
    for (const id of ['turb-sighted', 'turb-blind']) {
      assert.equal(nodes[id].textContent, '700 °C / 850 °C', `#${id} in English`);
      assert.equal(nodes[id].dir, 'ltr', `#${id} in English`);
    }
  } finally {
    nodes['lang-toggle'].click();
  }
});

// mountChase's try once wrapped setTheme and draw as well as the import and
// createChaseScene, so an error in the pause panel was shown as "the 3D view
// could not be shown" and the scene already built was left behind. Here the
// panel's heading throws on the first read after the scene is created.
test('an error after the chase scene is created is not shown as the WebGL message', async () => {
  const logged = [];
  const consoleError = console.error;
  console.error = err => { logged.push(err); };
  let armed = false;
  const heading = new FakeNode('h3');
  Object.defineProperty(heading, 'textContent', {
    get() { if (armed) { armed = false; throw new Error('pause panel failed'); } return ''; },
    set() {},
  });
  nodes['pause-heading'] = heading;
  nodes.chase = new FakeNode('div');
  globalThis.chaseFake.onCreate = () => { armed = true; };
  try {
    nodes.compute.click();
    // A meta for another episode, so the page mounts a chase view for it.
    reply(await nextRequest(), { status: 'ready', since: 0, frames: [], steps: 719, meta: { ...META, ep: 2 }, road: ROAD });
    await settle();
    assert.equal(globalThis.chaseFake.scenes.length, 1, 'the stand-in chase scene was created');
    assert.equal(armed, false, 'the panel was never drawn after the scene was created');
    assert.deepEqual(byClass(nodes.chase, 'webgl-error'), [], 'a pause-panel error was shown as the WebGL message');
    assert.equal(globalThis.chaseFake.scenes[0].disposed, false, 'the scene that was built is still the page\'s');
    assert.ok(logged.some(e => e?.message === 'pause panel failed'), 'the panel error is logged as itself');
  } finally {
    console.error = consoleError;
    globalThis.chaseFake.onCreate = null;
    delete nodes['pause-heading'];
  }
});

test('a chase scene that cannot be created shows the WebGL message in its place', async () => {
  const consoleError = console.error;
  console.error = () => {};
  globalThis.chaseFake.fail = 'no WebGL in this process';
  try {
    nodes.compute.click();
    reply(await nextRequest(), { status: 'ready', since: 0, frames: [], steps: 719, meta: { ...META, ep: 3 }, road: ROAD });
    await settle();
    const shown = byClass(nodes.chase, 'webgl-error');
    assert.equal(shown.length, 1, 'the chase view says it cannot draw');
    assert.match(shown[0].textContent, /ثلاثي الأبعاد/);
    assert.equal(globalThis.chaseFake.scenes[0].disposed, true, 'the previous episode\'s scene was disposed');
  } finally {
    console.error = consoleError;
    globalThis.chaseFake.fail = null;
    delete nodes.chase;
  }
});

// charts-lib.mjs, the results tab's copy of Ghassan's drawing helpers: its
// scales and ticks (pure), plot / markTip / showTip / sideLabel / crosshair on
// a fake DOM (charts-fake-dom.mjs), and createMounter with plain fake hosts, a
// stub ResizeObserver and a stub document; then results.css, read as text.
// node --test runs this file in its own process, so the globals it installs
// reach no other test file.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { FakeEl, installFakeDocument, fakeHost, walk, svgTexts } from './charts-fake-dom.mjs?v=R1a';
import {
  NS, S, fin, lin, logs, ticks, plot, line, hline, vline, showTip, hideTip,
  crosshair, nearest, markTip, sideLabel, createMounter,
} from './charts-lib.mjs?v=R1a';

// A ResizeObserver that records what it watches; fire() is a resize.
class StubRO {
  static all = [];
  constructor(cb) { this.cb = cb; this.observed = new Set(); this.disconnects = 0; StubRO.all.push(this); }
  observe(el) { this.observed.add(el); }
  unobserve(el) { this.observed.delete(el); }
  disconnect() { this.observed.clear(); this.disconnects += 1; }
  fire() { this.cb([]); }
}
// A document that records its listeners.
function stubDocument() {
  const doc = {
    added: [], removed: [],
    addEventListener(type, fn) { doc.added.push([type, fn]); },
    removeEventListener(type, fn) { doc.removed.push([type, fn]); },
  };
  globalThis.document = doc;
  return doc;
}
// The smallest host createMounter can draw into: a width and two queries.
const plainHost = width => ({ id: `host${width}`, clientWidth: width,
  querySelector: () => null, querySelectorAll: () => [] });
function newMounter(options) {
  StubRO.all.length = 0;
  globalThis.ResizeObserver = StubRO;
  return createMounter(options);
}

test('lin maps a domain onto a range and inverts it, either way round', () => {
  const s = lin(0, 10, 100, 200);
  assert.equal(s(0), 100);
  assert.equal(s(5), 150);
  assert.equal(s(10), 200);
  assert.equal(s.inv(150), 5);
  const y = lin(0, 800, 300, 12); // a y axis: a larger value is a smaller pixel
  assert.equal(y(0), 300);
  assert.equal(y(800), 12);
  assert.equal(y(400), 156);
  for (const v of [0, 123.4, 800]) assert.ok(Math.abs(y.inv(y(v)) - v) < 1e-9, `inv(${v})`);
  const lg = logs(1, 100, 0, 200);
  assert.ok(Math.abs(lg(10) - 100) < 1e-9);
  assert.ok(Math.abs(lg.inv(100) - 10) < 1e-9);
});

test('ticks are round steps inside the range, and none for an empty or reversed one', () => {
  assert.deepEqual(ticks(0, 1000, 5), [0, 200, 400, 600, 800, 1000]);
  assert.deepEqual(ticks(0, 778.14, 5), [0, 200, 400, 600]);
  assert.deepEqual(ticks(0, 1207.44, 5), [0, 200, 400, 600, 800, 1000, 1200]);
  assert.deepEqual(ticks(-0.5, 7.5, 8), [0, 1, 2, 3, 4, 5, 6, 7]);
  assert.deepEqual(ticks(0.1, 0.9, 4), [0.2, 0.4, 0.6, 0.8]);
  assert.deepEqual(ticks(3, 3, 5), []);
  assert.deepEqual(ticks(5, 1, 5), []);
});

test('fin accepts finite numbers only', () => {
  for (const v of [0, -3.5, 1e9]) assert.equal(fin(v), true, String(v));
  for (const v of [null, undefined, NaN, Infinity, -Infinity, '5']) assert.equal(fin(v), false, String(v));
});

test('plot draws its ticks and no axis title, never role="img", and returns its scales', () => {
  installFakeDocument();
  const host = fakeHost(600);
  const P = plot(host, {
    w: 600, h: 300,
    x: { d: [-0.5, 2.5], ticks: [0, 1, 2], fmt: i => `s${i}`, label: 'Seed' },
    y: { d: [0, 100], ticks: [0, 50, 100], label: 'Damage' },
    m: { l: 50, r: 20, t: 10, b: 30 },
  });
  assert.deepEqual(Object.keys(P).sort(), ['H', 'W', 'g', 'host', 'm', 'ph', 'pw', 'svg', 'top', 'x', 'y']);
  assert.equal(P.svg.tagName, 'svg');
  assert.equal(P.svg.namespaceURI, NS);
  assert.equal(P.svg.getAttribute('class'), 'rc-plot');
  assert.equal(P.svg.getAttribute('width'), '600');
  assert.equal(P.svg.getAttribute('height'), '300');
  assert.equal(P.svg.getAttribute('viewBox'), '0 0 600 300');
  assert.equal(P.svg.getAttribute('role'), null);
  assert.equal(P.svg.getAttribute('aria-label'), null);
  assert.deepEqual(svgTexts(host), ['s0', 's1', 's2', '0', '50', '100'], 'the axis titles are HTML, not SVG');
  assert.equal(P.x(-0.5), 50);
  assert.equal(P.x(2.5), 580);
  assert.equal(P.y(0), 270);
  assert.equal(P.y(100), 10);
  assert.equal(P.pw, 530);
  assert.equal(P.ph, 260);
  for (const el of walk(host)) {
    for (const c of el.classes()) assert.match(c, /^rc-/, `<${el.tagName}> carries the class ${c}`);
  }
  const labelled = plot(fakeHost(400), { w: 400, h: 250, x: { d: [0, 1] }, y: { d: [0, 1] }, aria: 'The pairs of C4' });
  assert.equal(labelled.svg.getAttribute('role'), 'group');
  assert.equal(labelled.svg.getAttribute('aria-label'), 'The pairs of C4');
  const clip = walk(labelled.svg).find(el => el.tagName === 'clipPath');
  assert.match(clip.getAttribute('id'), /^rc-clip\d+$/);
  assert.equal(labelled.g.getAttribute('clip-path'), `url(#${clip.getAttribute('id')})`);
});

test('line lifts the pen at a missing value; hline and vline span the plot', () => {
  installFakeDocument();
  const P = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  const p = line(P, [0, 5, NaN, 10, 10], [0, 5, 7, 10, 0], { c: 'var(--rc-grade)', dash: '5 4' });
  assert.equal(p.getAttribute('d'), 'M0.0,200.0L150.0,100.0M300.0,0.0L300.0,200.0');
  assert.equal(p.getAttribute('class'), 'rc-ln');
  assert.equal(p.getAttribute('style'), 'stroke:var(--rc-grade);stroke-width:2;stroke-dasharray:5 4;');
  const h = hline(P, 5, { c: 'var(--rc-mei)' });
  assert.deepEqual(['x1', 'x2', 'y1', 'y2'].map(k => h.getAttribute(k)), ['0', '300', '100', '100']);
  const v = vline(P, 5, { c: 'var(--rc-mei)', label: 'x' });
  assert.deepEqual(['x1', 'x2', 'y1', 'y2'].map(k => v.getAttribute(k)), ['150', '150', '0', '200']);
  assert.deepEqual(svgTexts(P.top), ['x']);
});

test('markTip makes a mark focusable and shows its rows on focus, hover and tap; blur hides them', () => {
  installFakeDocument();
  const host = fakeHost(300);
  const P = plot(host, { w: 300, h: 200, x: { d: [0, 1] }, y: { d: [0, 1] } });
  const dot = S('circle', { cx: 100, cy: 50, r: 5 }, P.g);
  markTip(P, dot, 100, 50, 'Seed 0', [{ c: 'var(--rc-sighted)', v: '359.9', k: 'median' }, { v: '+360.6', k: 'blind minus sighted' }]);
  assert.equal(dot.getAttribute('tabindex'), '0');
  assert.ok(dot.classList.contains('rc-mark'));
  for (const type of ['focus', 'pointerenter', 'pointerdown']) {
    hideTip(host);
    dot.dispatch(type, { pointerType: 'touch' });
    assert.equal(host.querySelector(':scope > .rc-tip').hidden, false, type);
  }
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.getAttribute('role'), 'status');
  assert.equal(host.querySelectorAll(':scope > .rc-tip').length, 1, 'one tip per chart, reused');
  const [title, first, second] = tipEl.children;
  assert.equal(title.getAttribute('class'), 'rc-tt');
  assert.equal(title.textContent, 'Seed 0');
  assert.equal(first.getAttribute('class'), 'rc-tr');
  assert.deepEqual(first.children.map(c => c.getAttribute('class')), ['rc-key', null, 'rc-tl']);
  assert.equal(first.children[0].style.borderColor, 'var(--rc-sighted)');
  assert.equal(first.children[1].tagName, 'b');
  assert.equal(first.children[1].textContent, '359.9');
  assert.equal(first.children[2].textContent, 'median');
  assert.equal(second.children[0].style.borderColor, 'transparent');
  dot.dispatch('pointerleave', { pointerType: 'touch' });
  assert.equal(tipEl.hidden, false, 'a finger lifting off keeps the numbers up');
  dot.dispatch('pointerleave', { pointerType: 'mouse' });
  assert.equal(tipEl.hidden, true);
  dot.dispatch('focus');
  dot.dispatch('blur');
  assert.equal(tipEl.hidden, true);
});

test('showTip keeps the tip inside its chart', () => {
  installFakeDocument();
  const host = fakeHost(300); // the fake tip is 120 x 60
  showTip(host, 250, 100, 'T', [{ v: '1' }]);
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.style.left, '116px', 'right edge: left of the point (250 - 14 - 120)');
  assert.equal(tipEl.style.top, '28px', 'above the point (100 - 60 - 12)');
  showTip(host, 20, 30, 'T', [{ v: '1' }]);
  assert.equal(tipEl.style.left, '34px', 'right of the point (20 + 14)');
  assert.equal(tipEl.style.top, '46px', 'top edge: below the point (30 + 16)');
});

test('sideLabel flips left only when its MEASURED width would leave the plot', () => {
  installFakeDocument();
  const P = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 1] }, y: { d: [0, 1] }, m: { l: 0, r: 20, t: 0, b: 0 } });
  try {
    FakeEl.textWidth = () => 40;
    const a = sideLabel(P, 200, 50, 'MEI'); // 200 + 14 + 40 = 254 < 280
    assert.deepEqual([a.getAttribute('x'), a.getAttribute('text-anchor')], ['214', 'start']);
    assert.equal(a.getAttribute('class'), 'rc-lbl');
    const b = sideLabel(P, 230, 50, 'MEI'); // 230 + 14 + 40 = 284: the 6.8 px guess (20.4) would have kept it right
    assert.deepEqual([b.getAttribute('x'), b.getAttribute('text-anchor')], ['216', 'end']);
    FakeEl.textWidth = () => 0; // nothing measured: 6.8 px a character
    const c = sideLabel(P, 230, 50, 'MEI'); // 230 + 14 + 20.4 = 264.4 < 280
    assert.equal(c.getAttribute('text-anchor'), 'start');
    const d = sideLabel(P, 240, 50, 'a much longer label'); // 19 x 6.8 = 129.2
    assert.equal(d.getAttribute('text-anchor'), 'end');
  } finally {
    FakeEl.textWidth = null;
  }
});

test('crosshair and nearest show the numbers of the point under the pointer', () => {
  installFakeDocument();
  const host = fakeHost(300);
  const P = plot(host, { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  crosshair(P, [0, 5, 10], [{ name: 'a', ys: [1, 2, 3], c: 'var(--rc-grade)', f: v => `v${v}` }], x => `x${x}`);
  const hit = P.top.children.find(el => el.classes().includes('rc-hit'));
  hit.dispatch('pointermove', { clientX: 140, clientY: 50 }); // 140 px is x 4.67: the nearest x is 5
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.children[0].textContent, 'x5');
  assert.equal(tipEl.children[1].children[1].textContent, 'v2');
  hit.dispatch('pointerleave', { pointerType: 'mouse' });
  assert.equal(tipEl.hidden, true);
  const Q = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  nearest(Q, [{ x: 2, y: 2, name: 'p' }, { x: 8, y: 8, name: 'q' }], p => ({ title: p.name, rows: [{ v: String(p.x) }] }));
  const hit2 = Q.top.children.find(el => el.classes().includes('rc-hit'));
  hit2.dispatch('pointermove', { clientX: 235, clientY: 45 }); // the point (8, 8) is at (240, 40)
  assert.equal(Q.host.querySelector(':scope > .rc-tip').children[0].textContent, 'q');
});

test('createMounter draws each chart at its width, with the default height rule or hOf', () => {
  stubDocument();
  const m = newMounter();
  const calls = [];
  const draw = (...args) => calls.push(args);
  const a = plainHost(600), b = plainHost(300), c = plainHost(1000), d = plainHost(800);
  m.mount(a, draw);
  m.mount(b, draw);
  m.mount(c, draw);
  m.mount(d, draw, w => w / 4);
  m.mount(null, draw); // a missing host is skipped
  assert.deepEqual(calls, [[a, 600, 336], [b, 300, 250], [c, 1000, 400], [d, 800, 200]]);
  m.dispose();
});

test('a zero width never draws; an unchanged width redraws only when forced; a resize redraws', () => {
  stubDocument();
  const m = newMounter();
  const calls = [];
  const host = plainHost(0);
  m.mount(host, (h, w, hh) => calls.push([w, hh]));
  m.renderAll();
  m.renderAll(true);
  assert.deepEqual(calls, [], 'a host with no width yet is not drawn, forced or not');
  host.clientWidth = 500;
  StubRO.all[0].fire();
  assert.deepEqual(calls, [[500, 280]], 'the observer draws it once it has a width');
  m.renderAll();
  assert.deepEqual(calls, [[500, 280]], 'same width: nothing to redraw');
  m.renderAll(true);
  assert.deepEqual(calls, [[500, 280], [500, 280]], 'forced (a language switch): redrawn');
  m.dispose();
});

test('a draw that throws reaches onError, and the other charts still draw', () => {
  stubDocument();
  const errors = [];
  const drawn = [];
  const m = newMounter({ onError: (host, err) => errors.push([host, err.message]) });
  const bad = plainHost(400), good = plainHost(400);
  m.mount(bad, () => { throw new Error('no data'); });
  m.mount(good, h => drawn.push(h));
  assert.deepEqual(errors, [[bad, 'no data']]);
  assert.deepEqual(drawn, [good]);
  m.dispose();
  const logged = [];
  const original = console.error;
  console.error = (...args) => logged.push(args);
  try {
    const quiet = newMounter();
    quiet.mount(plainHost(400), () => { throw new Error('boom'); });
    quiet.dispose();
  } finally {
    console.error = original;
  }
  assert.equal(logged.length, 1, 'the default hook logs and never throws');
});

test('one observer and one document listener; clear forgets every chart, dispose removes both', () => {
  const doc = stubDocument();
  const m = newMounter();
  assert.equal(StubRO.all.length, 1);
  assert.deepEqual(doc.added.map(([type]) => type), ['pointerdown']);
  const h1 = plainHost(400), h2 = plainHost(400);
  const drawn = [];
  m.mount(h1, h => drawn.push(h));
  m.mount(h2, h => drawn.push(h));
  assert.equal(StubRO.all.length, 1, 'still one observer for two charts');
  assert.deepEqual([...StubRO.all[0].observed], [h1, h2]);
  m.clear();
  assert.equal(StubRO.all[0].observed.size, 0);
  m.renderAll(true);
  assert.deepEqual(drawn, [h1, h2], 'a forgotten chart is not drawn again');
  m.mount(h1, h => drawn.push(h));
  assert.deepEqual([...StubRO.all[0].observed], [h1]);
  m.dispose();
  assert.equal(StubRO.all[0].disconnects, 1);
  assert.deepEqual(doc.removed, doc.added, 'the same listener is removed');
  m.renderAll(true);
  assert.equal(drawn.length, 3);
});

test('a pointerdown outside every chart hides every tip; one inside a chart does not', () => {
  const doc = installFakeDocument();
  const m = newMounter();
  const host = fakeHost(400);
  m.mount(host, (h, w, hh) => { plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } }); });
  showTip(host, 10, 10, 'T', []);
  const tipEl = host.querySelector(':scope > .rc-tip');
  doc.dispatch('pointerdown', { target: walk(host).find(el => el.tagName === 'svg') });
  assert.equal(tipEl.hidden, false, 'a tap inside a chart is the chart\'s own');
  doc.dispatch('pointerdown', { target: new FakeEl('p') });
  assert.equal(tipEl.hidden, true);
  m.dispose();
  assert.equal((doc.listeners.pointerdown || []).length, 0);
});

test('a redraw replaces the svg and hides the tip; a draw that throws leaves no half chart', () => {
  installFakeDocument();
  const m = newMounter();
  const host = fakeHost(400);
  m.mount(host, (h, w, hh) => plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } }));
  assert.equal(host.querySelectorAll(':scope > svg').length, 1);
  showTip(host, 5, 5, 'T', []);
  m.renderAll(true);
  assert.equal(host.querySelectorAll(':scope > svg').length, 1, 'one svg, not two');
  assert.equal(host.querySelector(':scope > .rc-tip').hidden, true);
  m.dispose();
  const errors = [];
  const m2 = newMounter({ onError: () => errors.push(1) });
  const half = fakeHost(400);
  m2.mount(half, (h, w, hh) => {
    plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } });
    throw new Error('half drawn');
  });
  assert.equal(half.querySelectorAll(':scope > svg').length, 0);
  assert.equal(errors.length, 1);
  m2.dispose();
});

// Hue and saturation of a #rrggbb colour.
function hueSat(hex) {
  const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min, l = (max + min) / 2;
  if (d === 0) return { h: 0, s: 0 };
  const h = max === r ? 60 * (((g - b) / d) % 6) : max === g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
  return { h: (h + 360) % 360, s: d / (1 - Math.abs(2 * l - 1)) };
}

test('results.css: every token in both themes, the resets of design 7.3, and no red or green', () => {
  const css = readFileSync(new URL('./results.css', import.meta.url), 'utf8');
  const block = selector => {
    const at = css.indexOf(selector);
    assert.ok(at >= 0, `missing ${selector}`);
    return css.slice(at, css.indexOf('}', at));
  };
  const light = block(':root{--rc-');
  const dark = block(':root[data-theme="dark"]{');
  const system = block(':root:not([data-theme="light"]){');
  for (const name of ['sighted', 'blind', 'baseline', 'reactive', 'grade', 'text', 'muted', 'grid', 'axis', 'tip-bg', 'tip-fg', 'mei']) {
    assert.ok(light.includes(`--rc-${name}:`), `--rc-${name} in the light block`);
  }
  assert.ok(light.includes('--rc-sighted:var(--agent-sighted'), 'sighted is agents.css\'s blue');
  assert.ok(light.includes('--rc-blind:var(--agent-blind'), 'blind is agents.css\'s amber');
  const pairs = [['baseline', '#5b6470', '#b9c0c8'], ['reactive', '#8a8f98', '#8d939a'], ['grade', '#6b4fa0', '#b9a3e8'],
    ['grid', '#e3e6e1', '#2a2f2e'], ['axis', '#c9cdc6', '#3a403f'], ['mei', '#4b4f56', '#c7ccd2']];
  for (const [name, day, night] of pairs) {
    assert.ok(light.includes(`--rc-${name}:${day}`), `light --rc-${name}`);
    assert.ok(dark.includes(`--rc-${name}:${night}`), `dark --rc-${name}`);
    assert.ok(system.includes(`--rc-${name}:${night}`), `system-dark --rc-${name}`);
  }
  for (const rule of [
    '.rc-chart > svg{width:auto;height:auto;fill:#000;stroke:none;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter}',
    '.rc-chart{position:relative;width:100%;height:auto;direction:ltr;touch-action:pan-y}',
    '.rc-plot text{stroke:none;font-family:Consolas,ui-monospace,monospace;font-size:11px;fill:var(--rc-muted)}',
    'html[dir=rtl] .rc-tip{direction:rtl}',
    '.rc-tip .rc-tl{white-space:normal}',
  ]) assert.ok(css.includes(rule), `missing ${rule}`);
  assert.doesNotMatch(css, /ellipsis/, 'a tooltip label is never cut');
  for (const cls of ['rc-plot', 'rc-grid', 'rc-axis', 'rc-ln', 'rc-hit', 'rc-hair', 'rc-hdot', 'rc-mark', 'rc-ring',
    'rc-lbl', 'rc-tip', 'rc-tt', 'rc-tr', 'rc-tl', 'rc-key', 'rc-dot', 'rc-pair', 'rc-band', 'rc-mei', 'rc-mei-label']) {
    assert.ok(css.includes(`.${cls}`), `no rule for .${cls}, a class the chart code writes`);
  }
  for (const hex of new Set(css.match(/#[0-9a-fA-F]{6}\b/g))) {
    const { h, s } = hueSat(hex);
    const redOrGreen = h >= 345 || h <= 15 || (h >= 80 && h <= 165);
    assert.ok(s < 0.25 || !redOrGreen, `${hex} reads as red or green (hue ${h.toFixed(0)}, saturation ${s.toFixed(2)})`);
  }
});

test('the drawing code writes every colour as a token, so a theme switch redraws nothing', () => {
  for (const name of ['charts-lib.mjs']) {
    const src = readFileSync(new URL(`./${name}`, import.meta.url), 'utf8');
    assert.doesNotMatch(src, /#[0-9a-fA-F]{3,6}\b|rgba?\(/, `${name} carries a literal colour`);
  }
});

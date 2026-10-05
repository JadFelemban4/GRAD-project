// results-charts.mjs: the layouts of the pairs chart and of the hand-written
// comparison (pure), their tooltip and table rows in both languages, and the
// two draw steps on a fake DOM (charts-lib.mjs through charts-fake-dom.mjs).
// The fixture is C4 as results/c4_seed0..7.txt print it.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './results-strings.mjs?v=R1a';
import { EM_DASH, MINUS, NNBSP } from './results-format.mjs?v=R1a';
import { installFakeDocument, fakeHost, walk, svgTexts } from './charts-fake-dom.mjs?v=R1a';
import {
  ROLE_VAR, HAND_ROLES, pairsLayout, handLayout, pairsTip, handTip, pairsTable, handTable,
  drawPairs, drawHand,
} from './results-charts.mjs?v=R1a';

// Built from code points, so no editor can turn them into look-alikes here.
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const iso = text => `${LRI}${text}${PDI}`;
const ARABIC = new RegExp(`[${String.fromCodePoint(0x600)}-${String.fromCodePoint(0x6ff)}]`);

// [seed, sighted, blind]: median, IQR width, worst, median fuel, peak, as each
// results/c4_seed<N>.txt prints them. Out of order on purpose.
const C4_ROWS = [
  [3, [336.1, 179.8, 964.1, 5264, 876], [349.5, 154.0, 721.0, 5225, 863]],
  [0, [359.9, 156.9, 674.3, 5162, 868], [720.5, 492.6, 1453.7, 4726, 912]],
  [7, [365.5, 344.7, 890.4, 5157, 866], [363.1, 233.9, 979.8, 5294, 874]],
  [1, [490.2, 263.7, 900.0, 4827, 876], [409.9, 246.4, 811.1, 5161, 875]],
  [5, [442.6, 326.8, 1399.8, 4862, 895], [442.3, 251.8, 984.8, 4840, 878]],
  [2, [602.2, 350.9, 1165.3, 4726, 890], [524.4, 299.2, 1598.4, 4786, 910]],
  [6, [357.6, 246.4, 967.1, 5049, 878], [347.6, 267.6, 1018.3, 5105, 876]],
  [4, [332.8, 164.0, 868.4, 5099, 875], [371.0, 151.6, 816.6, 4934, 868]],
];
// The hand-written rows: every C4 file prints the same three.
const C4_HAND = {
  baseline: ['baseline ECU', [1118.0, 715.9, 2363.8, 4818, 924]],
  reactive: ['reactive', [667.8, 214.5, 919.8, 5040, 871]],
  current_grade: ['current-grade', [653.5, 295.5, 907.0, 5158, 871]],
};
const policy = (label, dir, [median, iqr, worst, fuel, peak]) => ({ label, dir, median, iqr, worst, fuel, peak });

// An evaluation section as GET /api/results sends it (app/results_data.py).
function c4Section() {
  return {
    id: 'exp-c4', kind: 'evaluation', state: 'ok', prefix: 'c4', name: 'C4',
    mei: 50, mei_after_result: false, thermal_recorded: 'none',
    seeds: C4_ROWS.map(([seed, s, b]) => ({
      seed,
      file: `results/c4_seed${seed}.txt`,
      sighted: policy(`agent runs_c4\\sighted_seed${seed}`, `runs_c4/sighted_seed${seed}`, s),
      blind: policy(`agent (blind) runs_c4\\blind_seed${seed}`, `runs_c4/blind_seed${seed}`, b),
      baseline: policy(C4_HAND.baseline[0], null, C4_HAND.baseline[1]),
      reactive: policy(C4_HAND.reactive[0], null, C4_HAND.reactive[1]),
      current_grade: policy(C4_HAND.current_grade[0], null, C4_HAND.current_grade[1]),
      thermal: null,
      diff: b[0] - s[0],
      budget: { steps: 300000, requested: 300000 },
    })),
  };
}
const SEEDS = [0, 1, 2, 3, 4, 5, 6, 7];
const inside = (v, [lo, hi]) => v >= lo && v <= hi;

test('ROLE_VAR gives every role a colour token of results.css, and HAND_ROLES orders them as the files do', () => {
  assert.deepEqual(HAND_ROLES, ['baseline', 'reactive', 'current_grade', 'sighted', 'blind']);
  assert.deepEqual(Object.keys(ROLE_VAR).sort(), [...HAND_ROLES].sort());
  assert.deepEqual(ROLE_VAR, {
    sighted: 'var(--rc-sighted)', blind: 'var(--rc-blind)', baseline: 'var(--rc-baseline)',
    reactive: 'var(--rc-reactive)', current_grade: 'var(--rc-grade)',
  });
});

test('pairsLayout: the C4 pairs in seed order, every value inside the y domain', () => {
  const section = c4Section();
  const L = pairsLayout(section);
  assert.equal(L.empty, false);
  assert.equal(L.measure, 'total');
  assert.deepEqual(L.seeds, SEEDS);
  assert.deepEqual(L.x, { d: [-0.5, 7.5], ticks: SEEDS });
  assert.deepEqual(L.y.d, [0, 720.5 * 1.08]);
  assert.deepEqual(L.y.ticks, [0, 200, 400, 600]);
  const rows = new Map(C4_ROWS.map(([seed, s, b]) => [seed, { sighted: s, blind: b }]));
  assert.equal(L.marks.length, 16);
  for (const m of L.marks) {
    assert.equal(m.seed, L.seeds[m.i]);
    const [median, , worst, fuel, peak] = rows.get(m.seed)[m.role];
    assert.deepEqual([m.value, m.worst, m.fuel, m.peak], [median, worst, fuel, peak], `seed ${m.seed} ${m.role}`);
    assert.ok(Math.abs(m.x - m.i - (m.role === 'sighted' ? -0.12 : 0.12)) < 1e-12);
    assert.ok(inside(m.value, L.y.d), `seed ${m.seed} ${m.role} ${m.value} outside ${L.y.d}`);
  }
  assert.deepEqual(L.links.map(l => l.seed), SEEDS);
  for (const l of L.links) {
    const seed = section.seeds.find(s => s.seed === l.seed);
    assert.equal(l.a, seed.sighted.median);
    assert.equal(l.b, seed.blind.median);
    assert.equal(l.diff, l.b - l.a, 'blind minus sighted');
    assert.equal(l.diff, seed.diff, `seed ${l.seed}: the section's own difference`);
  }
  // As analyse_c4.py prints them: 3 of 8 positive.
  assert.deepEqual(L.links.map(l => Math.round(l.diff * 10) / 10), [360.6, -80.3, -77.8, 13.4, 38.2, -0.3, -10, -2.4]);
  assert.deepEqual(L.reference, { role: 'current_grade', values: Array(8).fill(653.5) });
  for (const v of L.reference.values) assert.ok(inside(v, L.y.d));
  assert.deepEqual(L.mei, { value: 50, afterResult: false });
  assert.deepEqual(L.svgLabels, [...SEEDS.map(String), '0', '200', '400', '600', 'MEI']);
  for (const s of L.svgLabels) assert.doesNotMatch(s, ARABIC);
  const phaseD = { ...section, mei_after_result: true };
  assert.deepEqual(pairsLayout(phaseD).mei, { value: 50, afterResult: true });
});

test('pairsLayout: the y domain reaches at least twice the MEI, so the bracket fits', () => {
  const section = c4Section();
  for (const s of section.seeds) {
    s.sighted.median = 10;
    s.blind.median = 12;
    s.current_grade.median = 20;
  }
  assert.deepEqual(pairsLayout(section).y.d, [0, 100]);
  const noMei = { ...section, mei: null };
  const L = pairsLayout(noMei);
  assert.deepEqual(L.y.d, [0, 20 * 1.08]);
  assert.equal(L.mei.value, null);
  assert.ok(!L.svgLabels.includes('MEI'));
  // No damage median is below zero, but the domain would still hold one.
  section.seeds[0].blind.median = -5;
  const below = pairsLayout(section);
  assert.equal(below.y.d[0], -5 * 1.08);
  for (const m of below.marks) assert.ok(inside(m.value, below.y.d), `${m.value} outside ${below.y.d}`);
  const hand = handLayout(section);
  for (const m of hand.marks) assert.ok(inside(m.value, hand.y.d), `${m.value} outside ${hand.y.d}`);
});

test('pairsLayout thermal: only the seeds whose files recorded both arms; none at all is empty', () => {
  const section = c4Section();
  const bySeed = Object.fromEntries(section.seeds.map(s => [s.seed, s]));
  bySeed[0].thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 }, current_grade: { median: 600, cut: 40 } };
  bySeed[2].thermal = { sighted: { median: 280, cut: 62 }, blind: { median: 250, cut: 66 }, current_grade: { median: 600, cut: 40 } };
  bySeed[1].thermal = { sighted: { median: 290, cut: 61 } };
  const L = pairsLayout(section, 'thermal');
  assert.equal(L.measure, 'thermal');
  assert.deepEqual(L.seeds, [0, 2]);
  assert.deepEqual(L.x, { d: [-0.5, 1.5], ticks: [0, 1] });
  assert.deepEqual(L.marks.map(m => [m.seed, m.role, m.value]),
    [[0, 'sighted', 300], [0, 'blind', 310.5], [2, 'sighted', 280], [2, 'blind', 250]]);
  for (const m of L.marks) assert.deepEqual([m.worst, m.fuel, m.peak], [null, null, null], 'no thermal worst, fuel or peak is recorded');
  assert.deepEqual(L.links.map(l => l.diff), [10.5, -30]);
  assert.deepEqual(L.reference, { role: 'current_grade', values: [600, 600] });
  assert.deepEqual(L.y.d, [0, 600 * 1.08]);
  for (const m of L.marks) assert.ok(inside(m.value, L.y.d));
  const none = pairsLayout(c4Section(), 'thermal');
  assert.equal(none.empty, true);
  assert.deepEqual([none.seeds, none.marks, none.links, none.svgLabels], [[], [], [], []]);
  assert.equal(none.reference, null);
});

test('pairsLayout refuses a measure it does not know', () => {
  assert.throws(() => pairsLayout(c4Section(), 'cut'), /unknown measure "cut"/);
});

test('handLayout: five policies per seed at their offsets, every value inside the domain', () => {
  const L = handLayout(c4Section());
  assert.equal(L.empty, false);
  assert.deepEqual(L.seeds, SEEDS);
  assert.deepEqual(L.roles, HAND_ROLES);
  assert.deepEqual(L.x, { d: [-0.5, 7.5], ticks: SEEDS });
  assert.deepEqual(L.y.d, [0, 1118.0 * 1.08]);
  assert.equal(L.marks.length, 40);
  const offset = { baseline: -0.3, reactive: -0.15, current_grade: 0, sighted: 0.15, blind: 0.3 };
  for (const m of L.marks) {
    assert.ok(Math.abs(m.x - (m.i + offset[m.role])) < 1e-12, `${m.role} at ${m.x}`);
    assert.ok(inside(m.value, L.y.d));
    assert.equal(m.seed, L.seeds[m.i]);
  }
  assert.deepEqual(L.marks.slice(0, 5).map(m => [m.role, m.value]),
    [['baseline', 1118.0], ['reactive', 667.8], ['current_grade', 653.5], ['sighted', 359.9], ['blind', 720.5]]);
  assert.deepEqual(L.svgLabels, [...SEEDS.map(String), '0', '200', '400', '600', '800', '1000', '1200']);
  const section = c4Section();
  section.seeds.find(s => s.seed === 4).reactive = null;
  const fewer = handLayout(section);
  assert.equal(fewer.marks.length, 39);
  assert.ok(!fewer.marks.some(m => m.seed === 4 && m.role === 'reactive'), 'a missing policy is left out, never drawn at zero');
  assert.equal(handLayout({ seeds: [] }).empty, true);
});

test('pairsTip: the median, worst, fuel, peak and the pair\'s difference, isolated in Arabic', () => {
  const L = pairsLayout(c4Section());
  const sighted0 = L.marks.find(m => m.seed === 0 && m.role === 'sighted');
  const en = pairsTip(L, sighted0, 'en');
  assert.equal(en.title, 'Sighted agent · Seed 0');
  assert.deepEqual(en.rows, [
    { c: 'var(--rc-sighted)', v: '359.9', k: t('en', 'results.tip.median') },
    { v: '674.3', k: t('en', 'results.tip.worst') },
    { v: `5${NNBSP}162`, k: t('en', 'results.tip.fuel') },
    { v: '868', k: t('en', 'results.tip.peak') },
    { v: '+360.6', k: t('en', 'results.tip.diff') },
  ]);
  const ar = pairsTip(L, sighted0, 'ar');
  assert.equal(ar.title, `${t('ar', 'results.legend.sighted')} · ${t('ar', 'results.tip.seed', { seed: iso('0') })}`);
  assert.deepEqual(ar.rows.map(r => r.v), [iso('359.9'), iso('674.3'), iso(`5${NNBSP}162`), iso('868'), iso('+360.6')]);
  assert.deepEqual(ar.rows.map(r => r.k), ['median', 'worst', 'fuel', 'peak', 'diff'].map(k => t('ar', `results.tip.${k}`)));
  const blind1 = L.marks.find(m => m.seed === 1 && m.role === 'blind');
  assert.equal(pairsTip(L, blind1, 'en').rows[0].c, 'var(--rc-blind)');
  assert.equal(pairsTip(L, blind1, 'en').rows.at(-1).v, `${MINUS}80.3`);
  assert.equal(pairsTip(L, blind1, 'ar').rows.at(-1).v, iso(`${MINUS}80.3`));
  const section = c4Section();
  section.seeds.find(s => s.seed === 0).thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 } };
  const T = pairsLayout(section, 'thermal');
  assert.deepEqual(pairsTip(T, T.marks[0], 'en').rows,
    [{ c: 'var(--rc-sighted)', v: '300.0', k: t('en', 'results.tip.median') }, { v: '+10.5', k: t('en', 'results.tip.diff') }]);
});

test('handTip: each policy\'s median, worst, fuel and peak, the engine computer by its legend name', () => {
  const L = handLayout(c4Section());
  const base = L.marks.find(m => m.seed === 0 && m.role === 'baseline');
  const en = handTip(L, base, 'en');
  assert.equal(en.title, 'Engine computer (modelled) · Seed 0');
  assert.deepEqual(en.rows, [
    { c: 'var(--rc-baseline)', v: '1118.0', k: t('en', 'results.tip.median') },
    { v: '2363.8', k: t('en', 'results.tip.worst') },
    { v: `4${NNBSP}818`, k: t('en', 'results.tip.fuel') },
    { v: '924', k: t('en', 'results.tip.peak') },
  ]);
  const ar = handTip(L, base, 'ar');
  assert.equal(ar.title, `${t('ar', 'results.legend.baseline')} · ${t('ar', 'results.tip.seed', { seed: iso('0') })}`);
  assert.deepEqual(ar.rows.map(r => r.v), [iso('1118.0'), iso('2363.8'), iso(`4${NNBSP}818`), iso('924')]);
  const grade = L.marks.find(m => m.seed === 7 && m.role === 'current_grade');
  assert.equal(handTip(L, grade, 'en').rows[0].c, 'var(--rc-grade)');
});

test('pairsTable and handTable: headers from the strings, one row per seed, cells isolated in Arabic', () => {
  const L = pairsLayout(c4Section());
  const keys = ['seed', 'sighted', 'blind', 'diff', 'sighted_worst', 'blind_worst', 'current_grade'];
  const en = pairsTable(L, 'en');
  assert.deepEqual(en.head, keys.map(k => t('en', `results.table.${k}`)));
  assert.equal(en.rows.length, 8);
  assert.deepEqual(en.rows[0], ['0', '359.9', '720.5', '+360.6', '674.3', '1453.7', '653.5']);
  assert.deepEqual(en.rows[1], ['1', '490.2', '409.9', `${MINUS}80.3`, '900.0', '811.1', '653.5']);
  const ar = pairsTable(L, 'ar');
  assert.deepEqual(ar.head, keys.map(k => t('ar', `results.table.${k}`)));
  assert.deepEqual(ar.rows[1], en.rows[1].map(iso));
  const section = c4Section();
  section.seeds.find(s => s.seed === 0).thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 } };
  const thermal = pairsTable(pairsLayout(section, 'thermal'), 'en');
  assert.deepEqual(thermal.head, ['seed', 'sighted', 'blind', 'diff', 'current_grade'].map(k => t('en', `results.table.${k}`)));
  assert.deepEqual(thermal.rows, [['0', '300.0', '310.5', '+10.5', EM_DASH]], 'no thermal current-grade recorded: a dash');
  const H = handLayout(c4Section());
  const hand = handTable(H, 'en');
  assert.deepEqual(hand.head, ['seed', 'baseline', 'reactive', 'current_grade', 'sighted', 'blind']
    .map(k => t('en', `results.table.${k}`)));
  assert.deepEqual(hand.rows.map(r => r[0]), SEEDS.map(String));
  assert.deepEqual(hand.rows[0], ['0', '1118.0', '667.8', '653.5', '359.9', '720.5']);
  assert.deepEqual(handTable(H, 'ar').rows[0], hand.rows[0].map(iso));
  const missing = c4Section();
  missing.seeds.find(s => s.seed === 0).reactive = null;
  assert.equal(handTable(handLayout(missing), 'en').rows[0][2], EM_DASH);
});

test('drawPairs writes exactly its layout\'s SVG labels, none of them Arabic, and one focusable mark per agent', () => {
  installFakeDocument();
  for (const lang of ['ar', 'en']) {
    const L = pairsLayout(c4Section());
    const host = fakeHost(640);
    const P = drawPairs(host, 640, 358, L, lang);
    assert.equal(P.svg.getAttribute('role'), null, 'the host, not the svg, carries the label');
    assert.deepEqual(svgTexts(host), L.svgLabels);
    for (const text of svgTexts(host)) assert.doesNotMatch(text, ARABIC, `${lang}: ${text}`);
    const marks = walk(host).filter(el => el.classes().includes('rc-mark'));
    assert.equal(marks.length, 16);
    marks.forEach((el, k) => {
      assert.equal(el.tagName, 'circle');
      assert.equal(el.getAttribute('tabindex'), '0');
      assert.equal(el.getAttribute('style'), `fill:${ROLE_VAR[L.marks[k].role]}`);
    });
    assert.equal(walk(host).filter(el => el.classes().includes('rc-pair')).length, 8, 'one link per pair');
    assert.equal(walk(host).filter(el => el.classes().includes('rc-mei')).length, 3, 'the MEI bracket');
    marks[0].dispatch('focus');
    const tipEl = host.querySelector(':scope > .rc-tip');
    assert.equal(tipEl.hidden, false);
    assert.equal(tipEl.children[0].textContent, pairsTip(L, L.marks[0], lang).title);
    assert.equal(tipEl.children[1].children[1].textContent, pairsTip(L, L.marks[0], lang).rows[0].v);
  }
});

test('drawPairs draws current-grade as one dashed line, or one dash per seed where the files differ', () => {
  installFakeDocument();
  const same = fakeHost(640);
  drawPairs(same, 640, 358, pairsLayout(c4Section()), 'en');
  const dashed = walk(same).filter(el => /stroke:var\(--rc-grade\)/.test(el.getAttribute('style') || ''));
  assert.deepEqual(dashed.map(el => el.tagName), ['line']);
  const section = c4Section();
  section.seeds.find(s => s.seed === 5).current_grade.median = 640.0;
  const differ = fakeHost(640);
  drawPairs(differ, 640, 358, pairsLayout(section), 'en');
  const path = walk(differ).find(el => el.tagName === 'path' && /--rc-grade/.test(el.getAttribute('style') || ''));
  assert.equal((path.getAttribute('d').match(/M/g) || []).length, 8);
});

test('drawHand writes exactly its SVG labels; squares for the hand-written policies, dots for the agents', () => {
  installFakeDocument();
  for (const lang of ['ar', 'en']) {
    const L = handLayout(c4Section());
    const host = fakeHost(900);
    drawHand(host, 900, 400, L, lang);
    assert.deepEqual(svgTexts(host), L.svgLabels);
    for (const text of svgTexts(host)) assert.doesNotMatch(text, ARABIC, `${lang}: ${text}`);
    const marks = walk(host).filter(el => el.classes().includes('rc-mark'));
    assert.equal(marks.length, 40);
    marks.forEach((el, k) => {
      const role = L.marks[k].role;
      assert.equal(el.tagName, role === 'sighted' || role === 'blind' ? 'circle' : 'rect', role);
      assert.equal(el.getAttribute('tabindex'), '0');
    });
    assert.equal(walk(host).filter(el => el.classes().includes('rc-band')).length, 4, 'every other seed banded');
    marks[2].dispatch('focus');
    assert.equal(host.querySelector(':scope > .rc-tip').children[0].textContent, handTip(L, L.marks[2], lang).title);
  }
});

test('an empty layout draws nothing', () => {
  installFakeDocument();
  const host = fakeHost(640);
  assert.equal(drawPairs(host, 640, 358, pairsLayout(c4Section(), 'thermal'), 'en'), null);
  assert.equal(drawHand(host, 640, 358, handLayout({ seeds: [] }), 'en'), null);
  assert.equal(host.children.length, 0);
});

test('no literal invisible character in the chart modules or their tests', () => {
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200e, 0x200f, 0x202f, 0x2212, 0x2011];
  for (const name of ['charts-lib.mjs', 'results-charts.mjs', 'charts-fake-dom.mjs', 'charts-lib.test.mjs', 'results-charts.test.mjs']) {
    const src = readFileSync(new URL(`./${name}`, import.meta.url), 'utf8');
    const found = [...src].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
    assert.deepEqual(found, [], `${name} carries a literal invisible character`);
  }
  const charts = readFileSync(new URL('./results-charts.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(charts, /#[0-9a-fA-F]{3,6}\b|rgba?\(/, 'a literal colour would not follow the theme');
});

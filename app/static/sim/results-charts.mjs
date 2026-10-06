// The results tab's two R1a figures (/results): the pairs chart (each seed's
// sighted and blind agent, joined, beside current-grade and the MEI) and the
// comparison with the hand-written policies from the same files.
//
// Each figure is a PURE layout function (domains, marks, tooltip rows, table
// rows), tested under node without a browser, and a thin draw step that turns
// a layout into SVG through charts-lib.mjs. Nothing here computes a statistic:
// every value is a median, a worst episode, a fuel or a peak that a result
// file records (GET /api/results), and the one difference, blind minus sighted
// per seed, is the one the analysis scripts print (design 5.1), so it is given
// for the total damage only: no script prints it without the knock term. No
// mean, no winner, nothing summed or averaged across experiments.
//
// SVG text holds numbers and the Latin "MEI" only. Every word of a figure, in
// either language, is HTML (the title, the axis titles, the legend, the
// tooltip, the table), so the bidi algorithm never reorders a chart label
// (design 7.3). layout.svgLabels lists every string a draw step writes as SVG
// text, and results-charts.test.mjs holds both draw steps to it.
//
// Every mark carries its x, and y carries its ticks, so a layout knows every
// SVG label before anything is drawn; handLayout also lists the roles it drew,
// for the legend.
import { t } from './i18n.mjs';
import { fmtNum, fmtSigned, fmtInt, inline } from './results-format.mjs?v=R1a';
import { S, T, plot, line, hline, markTip, fin, ticks } from './charts-lib.mjs?v=R1a';

export const ROLE_VAR = {
  sighted: 'var(--rc-sighted)', blind: 'var(--rc-blind)',
  baseline: 'var(--rc-baseline)', reactive: 'var(--rc-reactive)', current_grade: 'var(--rc-grade)',
};
export const HAND_ROLES = ['baseline', 'reactive', 'current_grade', 'sighted', 'blind'];

const MEASURES = ['total', 'thermal'];
// The sighted mark sits this far left of its seed and the blind one this far
// right, so two close medians never hide each other.
const PAIR_DX = 0.12;
const HAND_DX = { baseline: -0.3, reactive: -0.15, current_grade: 0, sighted: 0.15, blind: 0.3 };
const AGENTS = new Set(['sighted', 'blind']);
const Y_TICKS = 5;
const SEP = ' · ';
const HAND_HEAD = {
  baseline: 'results.table.baseline', reactive: 'results.table.reactive',
  current_grade: 'results.table.current_grade', sighted: 'results.table.sighted', blind: 'results.table.blind',
};

const orNull = v => (fin(v) ? v : null);
const medianOf = p => (p && fin(p.median) ? p.median : null);
const valueOf = (seed, role, measure) =>
  (measure === 'thermal' ? medianOf(seed?.thermal?.[role]) : medianOf(seed?.[role]));
const seedsOf = section => (section?.seeds || []).filter(s => s && Number.isInteger(s.seed));

// Zero (or the lowest value, were one ever below zero) to the highest value
// plus 8 %; with an MEI, at least twice the MEI, so its bracket always fits.
function yDomain(values, mei) {
  const vals = values.filter(fin);
  const lo = Math.min(0, ...vals);
  let hi = Math.max(0, ...vals) * 1.08;
  if (fin(mei) && mei > 0) hi = Math.max(hi, 2 * mei);
  if (!(hi > lo)) hi = lo + 1;
  return [lo < 0 ? lo * 1.08 : 0, hi];
}

// One format for every tick of an axis: as many decimals as the finest tick.
function tickFormat(yt) {
  const digits = Math.max(0, ...yt.map(v => (String(v).split('.')[1] || '').length));
  return v => fmtNum(v, Math.min(digits, 3));
}

function axes(seeds, yd) {
  const yt = seeds.length ? ticks(yd[0], yd[1], Y_TICKS) : [];
  return {
    x: { d: [-0.5, seeds.length - 0.5], ticks: seeds.map((_, i) => i) },
    y: { d: yd, ticks: yt },
    labels: seeds.length ? [...seeds.map(String), ...yt.map(tickFormat(yt))] : [],
  };
}

/**
 * The pairs of one evaluation section. measure 'total' reads each policy's
 * median damage and keeps every seed of the section: an arm whose file
 * printed no usable median (nan or inf, sent as null) gets no mark, and a seed
 * without both arms gets no link, but it stays on the axis and in the numbers
 * table, never dropped (design 4.1). measure 'thermal' reads the median
 * without the knock term (seed.thermal[role].median) and keeps only the seeds
 * whose files recorded it for both arms (the section names the others).
 * Seeds ascending. The difference blind minus sighted is given for 'total'
 * only (design 5.1).
 */
export function pairsLayout(section, measure = 'total') {
  if (!MEASURES.includes(measure)) throw new Error(`pairsLayout: unknown measure "${measure}"`);
  const total = measure === 'total';
  const rows = seedsOf(section)
    .map(s => ({ s, a: valueOf(s, 'sighted', measure), b: valueOf(s, 'blind', measure) }))
    .filter(r => total || (r.a !== null && r.b !== null))
    .sort((p, q) => p.s.seed - q.s.seed);
  const seeds = rows.map(r => r.s.seed);
  const marks = [];
  const links = [];
  rows.forEach(({ s, a, b }, i) => {
    for (const [role, value, dx] of [['sighted', a, -PAIR_DX], ['blind', b, PAIR_DX]]) {
      if (value === null) continue;
      const p = s[role] || {};
      marks.push({
        i, seed: s.seed, role, x: i + dx, value,
        worst: total ? orNull(p.worst) : null,
        fuel: total ? orNull(p.fuel) : null,
        peak: total ? orNull(p.peak) : null,
      });
    }
    if (a !== null && b !== null) links.push({ i, seed: s.seed, a, b, diff: total ? b - a : null });
  });
  const refs = rows.map(({ s }) => valueOf(s, 'current_grade', measure));
  const reference = refs.some(v => v !== null) ? { role: 'current_grade', values: refs } : null;
  const mei = { value: orNull(section?.mei), afterResult: Boolean(section?.mei_after_result) };
  const drawn = marks.length > 0;
  const ax = axes(drawn ? seeds : [], yDomain([...rows.flatMap(r => [r.a, r.b]), ...refs], mei.value));
  return {
    empty: !drawn, measure, seeds: drawn ? seeds : [],
    x: ax.x, y: ax.y, marks, links, reference, mei,
    svgLabels: drawn ? [...ax.labels, ...(mei.value !== null ? ['MEI'] : [])] : [],
  };
}

/**
 * Every policy of each seed's file, side by side: per seed index i, one mark
 * per role of HAND_ROLES that has a median, at x = i + its offset.
 */
export function handLayout(section) {
  const rows = seedsOf(section).sort((p, q) => p.seed - q.seed);
  const seeds = rows.map(s => s.seed);
  const marks = [];
  rows.forEach((s, i) => {
    for (const role of HAND_ROLES) {
      const p = s[role];
      const value = medianOf(p);
      if (value === null) continue;
      marks.push({ i, seed: s.seed, role, x: i + HAND_DX[role], value,
        worst: orNull(p.worst), fuel: orNull(p.fuel), peak: orNull(p.peak) });
    }
  });
  const ax = axes(marks.length ? seeds : [], yDomain(marks.map(m => m.value), null));
  return {
    empty: marks.length === 0, seeds: marks.length ? seeds : [],
    roles: HAND_ROLES.filter(r => marks.some(m => m.role === r)),
    x: ax.x, y: ax.y, marks, svgLabels: ax.labels,
  };
}

// "<role> · Seed <n>": two labels side by side, the seed number isolated in
// Arabic like every number in an Arabic line.
function tipTitle(role, seed, lang) {
  return `${t(lang, `results.legend.${role}`)}${SEP}${t(lang, 'results.tip.seed', { seed: inline(lang, String(seed)) })}`;
}
function medianRow(mark, lang) {
  return { c: ROLE_VAR[mark.role], v: inline(lang, fmtNum(mark.value, 1)), k: t(lang, 'results.tip.median') };
}
function detailRows(mark, lang) {
  return [
    { v: inline(lang, fmtNum(mark.worst, 1)), k: t(lang, 'results.tip.worst') },
    { v: inline(lang, fmtInt(mark.fuel)), k: t(lang, 'results.tip.fuel') },
    { v: inline(lang, fmtInt(mark.peak)), k: t(lang, 'results.tip.peak') },
  ];
}

/** The tooltip of one pairs mark: its median, (total only) worst, fuel, peak and its pair's blind minus sighted. */
export function pairsTip(layout, mark, lang) {
  const rows = [medianRow(mark, lang)];
  if (layout.measure === 'total') rows.push(...detailRows(mark, lang));
  const link = layout.links.find(l => l.i === mark.i);
  if (link && link.diff !== null) rows.push({ v: inline(lang, fmtSigned(link.diff, 1)), k: t(lang, 'results.tip.diff') });
  return { title: tipTitle(mark.role, mark.seed, lang), rows };
}

/** The tooltip of one mark of the hand-written comparison. */
export function handTip(layout, mark, lang) {
  return { title: tipTitle(mark.role, mark.seed, lang), rows: [medianRow(mark, lang), ...detailRows(mark, lang)] };
}

/** "The numbers" under the pairs chart: one row per seed on its axis, an em dash where a value is missing. */
export function pairsTable(layout, lang) {
  const total = layout.measure === 'total';
  const head = ['results.table.seed', 'results.table.sighted', 'results.table.blind',
    ...(total ? ['results.table.diff', 'results.table.sighted_worst', 'results.table.blind_worst'] : []),
    'results.table.current_grade'].map(k => t(lang, k));
  const rows = layout.seeds.map((seed, i) => {
    const mark = role => layout.marks.find(m => m.i === i && m.role === role) || null;
    const link = layout.links.find(l => l.i === i) || null;
    const ref = layout.reference ? layout.reference.values[i] : null;
    return [String(seed), fmtNum(mark('sighted')?.value ?? null, 1), fmtNum(mark('blind')?.value ?? null, 1),
      ...(total ? [fmtSigned(link ? link.diff : null, 1), fmtNum(mark('sighted')?.worst ?? null, 1),
        fmtNum(mark('blind')?.worst ?? null, 1)] : []),
      fmtNum(ref, 1)].map(text => inline(lang, text));
  });
  return { head, rows };
}

/** "The numbers" under the hand-written comparison: every policy's median per seed. */
export function handTable(layout, lang) {
  const head = ['results.table.seed', ...HAND_ROLES.map(r => HAND_HEAD[r])].map(k => t(lang, k));
  const rows = layout.seeds.map((seed, i) => [String(seed), ...HAND_ROLES.map(role => {
    const m = layout.marks.find(x => x.i === i && x.role === role);
    return fmtNum(m ? m.value : null, 1);
  })].map(text => inline(lang, text)));
  return { head, rows };
}

function frame(host, w, h, layout, right) {
  return plot(host, {
    w, h,
    x: { d: layout.x.d, ticks: layout.x.ticks, fmt: i => String(layout.seeds[i]) },
    y: { d: layout.y.d, ticks: layout.y.ticks, fmt: tickFormat(layout.y.ticks) },
    xgrid: false,
    m: { t: 12, r: right, b: 28, l: 52 },
  });
}

// The MEI as a length beside the plot: a bracket as tall as the MEI, labelled
// with the Latin abbreviation only; the HTML legend says what it is.
function drawMei(P, layout) {
  const mei = layout.mei.value;
  const lo = Math.max(layout.y.d[0], 0);
  const base = lo + (layout.y.d[1] - lo - mei) * 0.25;
  const x = P.W - P.m.r + 14;
  const y0 = P.y(base), y1 = P.y(base + mei);
  S('line', { x1: x, x2: x, y1: y0, y2: y1, class: 'rc-mei' }, P.top);
  S('line', { x1: x - 4, x2: x + 4, y1: y0, y2: y0, class: 'rc-mei' }, P.top);
  S('line', { x1: x - 4, x2: x + 4, y1: y1, y2: y1, class: 'rc-mei' }, P.top);
  T(P.top, x + 7, (y0 + y1) / 2 + 4, 'MEI', { class: 'rc-lbl rc-mei-label' });
}

/** The pairs chart into `host` at w x h. Returns the plot, or null for an empty layout. */
export function drawPairs(host, w, h, layout, lang) {
  if (!layout || layout.empty) return null;
  const P = frame(host, w, h, layout, w < 520 ? 46 : 64);
  const ref = layout.reference;
  if (ref) {
    const style = { c: ROLE_VAR.current_grade, w: 1.6, dash: '6 4' };
    const vals = ref.values.filter(fin);
    if (vals.length === ref.values.length && vals.every(v => v === vals[0])) {
      hline(P, vals[0], style);
    } else {
      const xs = [], ys = [];
      ref.values.forEach((v, i) => { xs.push(i - 0.42, i + 0.42, NaN); ys.push(v, v, NaN); });
      line(P, xs, ys, style);
    }
  }
  for (const l of layout.links) {
    S('line', { x1: P.x(l.i - PAIR_DX), y1: P.y(l.a), x2: P.x(l.i + PAIR_DX), y2: P.y(l.b), class: 'rc-pair' }, P.g);
  }
  const r = Math.max(3.5, Math.min(6.5, (P.pw / Math.max(1, layout.seeds.length)) * 0.09));
  for (const m of layout.marks) {
    const cx = P.x(m.x), cy = P.y(m.value);
    const dot = S('circle', { cx, cy, r, class: 'rc-dot', style: `fill:${ROLE_VAR[m.role]}` }, P.g);
    const tipRows = pairsTip(layout, m, lang);
    markTip(P, dot, cx, cy, tipRows.title, tipRows.rows);
  }
  if (layout.mei.value !== null) drawMei(P, layout);
  return P;
}

/** The hand-written comparison into `host` at w x h. Returns the plot, or null for an empty layout. */
export function drawHand(host, w, h, layout, lang) {
  if (!layout || layout.empty) return null;
  const P = frame(host, w, h, layout, 16);
  layout.seeds.forEach((_, i) => {
    if (i % 2) S('rect', { x: P.x(i - 0.5), y: P.m.t, width: P.x(i + 0.5) - P.x(i - 0.5), height: P.ph, class: 'rc-band' }, P.g);
  });
  const r = Math.max(2.5, Math.min(5.5, (P.pw / Math.max(1, layout.seeds.length)) * 0.06));
  for (const m of layout.marks) {
    const cx = P.x(m.x), cy = P.y(m.value);
    const style = `fill:${ROLE_VAR[m.role]}`;
    const el = AGENTS.has(m.role)
      ? S('circle', { cx, cy, r, class: 'rc-dot', style }, P.g)
      : S('rect', { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r, class: 'rc-dot', style }, P.g);
    const tipRows = handTip(layout, m, lang);
    markTip(P, el, cx, cy, tipRows.title, tipRows.rows);
  }
  return P;
}

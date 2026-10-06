// The results tab (/results): fetch, render, language, theme.
//
// PRESENTATION ONLY. The server (app/results_data.py) reads results/ on every
// request and sends values; results-view.mjs chooses each sentence and
// results-charts.mjs lays out and draws each figure. This file builds the DOM
// from them and computes nothing: no statistic, no average across
// experiments, no winner. Each experiment is its own section, never counted
// together with another.
//
// A language switch rebuilds every section and redraws every chart (the SVG
// labels hold no words, but the tooltips and tables do); a theme switch
// redraws nothing, because every colour is a CSS variable. Nothing is stored
// in the browser except the lab's own theme and language preferences and, in
// this tab's sessionStorage until the page is next built, the reader's place.
import './results-strings.mjs?v=R1a';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { inline } from './results-format.mjs?v=R1a';
import { createMounter } from './charts-lib.mjs?v=R1a';
import {
  ROLE_VAR, HAND_ROLES, pairsLayout, handLayout, pairsTable, handTable, drawPairs, drawHand,
} from './results-charts.mjs?v=R1a';
import {
  sectionName, nameSlot, metaText, plantView, verdictView, noteItems, summaryRows, unavailableText,
  notReadItems, builtView, checkItems, unpairedItems, thermalNote, meiLines,
} from './results-view.mjs?v=R1a';

const $ = id => document.getElementById(id);
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };
const PLACE_KEY = 'grad.results.place';
const ARMS = ['sighted', 'blind'];

let currentLang = DEFAULT_LANG;
const state = {
  payload: null,   // GET /api/results, once it has arrived
  failure: null,   // what to put in {status} when it did not
};
const mounter = createMounter({ onError: chartFailed });

function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* a preference is a convenience */ }
}
function recall(key, allowed, fallback) {
  try {
    const v = localStorage.getItem(key);
    return allowed.includes(v) ? v : fallback;
  } catch (e) { return fallback; }
}
function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function list(className, items) {
  const ul = el('ul', className);
  for (const item of items) ul.appendChild(el('li', '', item));
  return ul;
}

// A chart whose drawing throws says so in its own host, in the page's language.
function chartFailed(host, err) {
  console.error(err);
  host.querySelector(':scope > .rc-chart-error')?.remove();
  host.appendChild(el('p', 'rc-chart-error', t(currentLang, 'results.chart.unavailable')));
}

// ------------------------------------------------------------- the frame
function renderBuilt() {
  const built = $('built');
  const warnings = $('warnings');
  if (!built || !warnings) return;
  if (state.failure !== null) {
    built.hidden = true;
    warnings.hidden = true;
    return;
  }
  if (!state.payload) return;   // still loading: the markup's own line stands
  built.removeAttribute('data-i18n');
  const view = builtView(state.payload.built, state.payload.import_failures, currentLang);
  setText(built, view.line);
  warnings.textContent = '';
  for (const w of view.warnings) warnings.appendChild(el('li', '', w));
  warnings.hidden = view.warnings.length === 0;
}

function renderError() {
  const box = $('error');
  if (!box) return;
  box.hidden = state.failure === null;
  setText(box, state.failure === null ? ''
    : t(currentLang, 'results.error.fetch', { status: inline(currentLang, state.failure) }));
}

function renderSummary() {
  const rows = $('summary-rows');
  const summary = $('summary');
  if (!rows || !summary) return;
  rows.textContent = '';
  if (!state.payload) { summary.hidden = true; return; }
  for (const row of summaryRows(state.payload, currentLang)) {
    const tr = el('tr');
    const name = el('td', 'rc-summary-name');
    const link = el('a', 'rc-summary-link', row.name);
    link.href = `#${row.id}`;
    name.appendChild(link);
    for (const marker of row.markers) name.appendChild(el('p', 'rc-meta', marker));
    tr.append(name, el('td', 'rc-summary-plant', row.plant), el('td', 'rc-summary-verdict', row.verdict));
    rows.appendChild(tr);
  }
  summary.hidden = false;
}

function renderNotRead() {
  const box = $('not-read');
  const ul = $('not-read-list');
  if (!box || !ul) return;
  ul.textContent = '';
  const items = state.payload ? notReadItems(state.payload.not_read, currentLang) : [];
  for (const item of items) {
    const li = el('li');
    const path = el('code', '', item.path);
    path.dir = 'ltr';
    li.append(path, el('span', '', item.reason));
    ul.appendChild(li);
  }
  box.hidden = items.length === 0;
}

// ----------------------------------------------------------- a section
function verdictBlock(verdict, fold) {
  const view = verdictView(verdict, currentLang);
  const box = el('section', 'rc-verdict');
  box.dataset.state = view.state;
  box.appendChild(el('h3', '', t(currentLang, 'results.verdict.heading')));
  box.appendChild(el('p', 'verdict-short', view.short));
  const cells = el('ul', 'verdict-cells');
  for (const c of view.cells) {
    const li = el('li');
    const cell = el('b', 'cell', c.cell);
    cell.dir = 'ltr';
    li.append(cell, el('span', 'gloss', c.gloss));
    cells.appendChild(li);
  }
  box.appendChild(cells);
  if (view.lines.length) {
    const more = el('details', 'rc-verdict-lines');
    more.dataset.fold = fold;
    more.appendChild(el('summary', '', t(currentLang, 'results.verdict.lines')));
    for (const line of view.lines) {
      const fig = el('figure', 'quote');
      const pre = el('pre', '', line.text);
      pre.dir = 'ltr';
      const cite = el('figcaption', '', line.cite);
      cite.dir = 'ltr';
      fig.append(pre, cite);
      more.appendChild(fig);
    }
    box.appendChild(more);
  }
  return box;
}

// The legend, in HTML because every word of a chart is HTML (spec 7.3): the
// agents are dots, the hand-written policies squares, current-grade's
// reference a dash, and the MEI bracket is explained beside its own sign.
function legend(kind, layout, section) {
  const box = el('div', 'rc-legend');
  const item = (shape, colour, text) => {
    const span = el('span', 'rc-legend-item');
    const swatch = el('i', `rc-swatch ${shape}`);
    swatch.style.color = colour;
    span.append(swatch, el('span', '', text));
    box.appendChild(span);
  };
  if (kind === 'hand') {
    const roles = layout.roles || HAND_ROLES.filter(role => layout.marks.some(m => m.role === role));
    for (const role of roles) {
      item(ARMS.includes(role) ? 'rc-sw-dot' : 'rc-sw-square', ROLE_VAR[role], t(currentLang, `results.legend.${role}`));
    }
    return box;
  }
  for (const role of ARMS) item('rc-sw-dot', ROLE_VAR[role], t(currentLang, `results.legend.${role}`));
  if (layout.reference) item('rc-sw-dash', ROLE_VAR.current_grade, t(currentLang, 'results.legend.current_grade'));
  const mei = meiLines(section, currentLang);
  if (mei.length) item('rc-sw-bracket', 'var(--rc-mei)', mei.join(' '));
  return box;
}

function numbersTable(table, fold) {
  const details = el('details', 'rc-table');
  details.dataset.fold = fold;
  details.appendChild(el('summary', '', t(currentLang, 'results.table.toggle')));
  const tbl = el('table');
  const head = el('tr');
  for (const h of table.head) head.appendChild(el('th', '', h));
  const thead = el('thead');
  thead.appendChild(head);
  const tbody = el('tbody');
  for (const row of table.rows) {
    const tr = el('tr');
    for (const cell of row) tr.appendChild(el('td', '', cell));
    tbody.appendChild(tr);
  }
  tbl.append(thead, tbody);
  details.appendChild(tbl);
  return details;
}

const FIGURES = {
  pairs: { title: 'results.chart.pairs.title', what: 'results.chart.pairs.what', axis: 'results.chart.axis.damage',
    aria: 'results.chart.aria.pairs', measure: 'total' },
  'pairs-thermal': { title: 'results.chart.pairs_thermal.title', what: 'results.chart.pairs.what',
    axis: 'results.chart.axis.damage_thermal', aria: 'results.chart.aria.pairs', measure: 'thermal' },
  hand: { title: 'results.chart.hand.title', what: 'results.chart.hand.what', axis: 'results.chart.axis.damage',
    aria: 'results.chart.aria.hand' },
};

// One figure: title, what it shows, axis titles, the chart host, legend and
// the folded numbers. Returns the chart to mount once the node is in the page.
function figure(section, kind) {
  const spec = FIGURES[kind];
  const fig = el('figure', 'rc-figure');
  fig.dataset.figure = kind;
  fig.appendChild(el('h3', '', t(currentLang, spec.title)));
  fig.appendChild(el('p', 'rc-what', t(currentLang, spec.what)));
  try {
    const hand = kind === 'hand';
    const layout = hand ? handLayout(section) : pairsLayout(section, spec.measure);
    if (kind === 'pairs-thermal') {
      const note = thermalNote(section, currentLang);
      if (note) fig.appendChild(el('p', 'rc-note', note));
    }
    fig.appendChild(el('div', 'rc-axis-y', t(currentLang, spec.axis)));
    const host = el('div', 'rc-chart');
    // A group, not an image: the marks inside are focusable (spec 7.3).
    host.setAttribute('role', 'group');
    host.setAttribute('aria-label', t(currentLang, spec.aria, { name: nameSlot(section, currentLang) }));
    fig.appendChild(host);
    fig.appendChild(el('div', 'rc-axis-x', t(currentLang, 'results.chart.axis.seed')));
    fig.appendChild(legend(kind, layout, section));
    fig.appendChild(numbersTable(hand ? handTable(layout, currentLang) : pairsTable(layout, currentLang),
      `${section.id}:${kind}`));
    if (layout.empty) {
      host.appendChild(el('p', 'rc-chart-error', t(currentLang, 'results.chart.unavailable')));
      return { node: fig, chart: null };
    }
    const lang = currentLang;
    const draw = hand
      ? (node, w, h) => drawHand(node, w, h, layout, lang)
      : (node, w, h) => drawPairs(node, w, h, layout, lang);
    return { node: fig, chart: { host, draw } };
  } catch (err) {
    console.error(err);
    fig.appendChild(el('p', 'rc-note', t(currentLang, 'results.chart.unavailable')));
    return { node: fig, chart: null };
  }
}

function okSection(section, markers) {
  const node = el('article', 'rc-section');
  node.id = section.id;
  node.dataset.state = 'ok';
  node.appendChild(el('h2', '', sectionName(section, currentLang)));
  node.appendChild(el('p', 'rc-meta', metaText(section, currentLang)));
  for (const marker of markers) node.appendChild(el('p', 'rc-meta', marker));
  if (section.scenario) {
    // The scenario line as evaluate.py printed it: quoted, left to right.
    const quote = el('p', 'rc-meta rc-scenario', section.scenario);
    quote.dir = 'ltr';
    node.appendChild(quote);
  }
  const plant = plantView(section.provenance, currentLang);
  const line = el('p', 'rc-plant');
  line.dataset.state = plant.state;
  line.append(el('b', '', t(currentLang, 'results.plant.label')), ': ', el('span', '', plant.text));
  node.appendChild(line);
  node.appendChild(list('rc-plant-details', plant.details));
  node.appendChild(list('rc-checks', checkItems(section.checks, currentLang)));
  node.appendChild(verdictBlock(section.verdict, `${section.id}:verdict`));
  const notesHeading = el('p', 'rc-note rc-notes-heading');
  notesHeading.appendChild(el('b', '', t(currentLang, 'results.notes.heading')));
  node.appendChild(notesHeading);
  node.appendChild(list('rc-notes', noteItems(section.notes, currentLang)));
  const charts = [];
  const add = kind => {
    const f = figure(section, kind);
    node.appendChild(f.node);
    if (f.chart) charts.push(f.chart);
  };
  add('pairs');
  if (section.thermal_recorded !== 'none') add('pairs-thermal');
  else node.appendChild(el('p', 'rc-note', t(currentLang, 'results.chart.thermal_none')));
  add('hand');
  node.appendChild(list('rc-unpaired', unpairedItems(section.unpaired, currentLang)));
  return { node, charts };
}

function unavailableSection(section, text) {
  const node = el('article', 'rc-section');
  node.id = section.id;
  node.dataset.state = 'unavailable';
  node.append(el('h2', '', sectionName(section, currentLang)), el('p', 'rc-note rc-unavailable', text));
  return { node, charts: [] };
}

// A section that cannot be built costs only itself, never the tab.
function buildSection(section, markers) {
  if (section.state !== 'ok') return unavailableSection(section, unavailableText(section.error, currentLang));
  try {
    return okSection(section, markers);
  } catch (err) {
    console.error(err);
    return unavailableSection(section, unavailableText({ kind: 'build', type: err?.name }, currentLang));
  }
}

// Builds every section and returns its charts; render() mounts them.
function renderSections() {
  const host = $('sections');
  if (!host) return [];
  host.textContent = '';
  const rows = summaryRows(state.payload, currentLang);
  const charts = [];
  for (const section of state.payload?.sections || []) {
    const markers = rows.find(r => r.id === section.id)?.markers || [];
    const built = buildSection(section, markers);
    host.appendChild(built.node);
    charts.push(...built.charts);
  }
  return charts;
}

// The reader's place before a rebuild (a language switch): the section at the
// top of the viewport with its offset, and every open fold. At the very top of
// the page there is no section to hold.
function readPlace() {
  const top = window.scrollY > 0
    ? [...document.querySelectorAll('#sections > .rc-section')].find(s => s.getBoundingClientRect().bottom > 0)
    : null;
  return {
    id: top ? top.id : null,
    offset: top ? top.getBoundingClientRect().top : 0,
    open: new Set([...document.querySelectorAll('details[data-fold][open]')].map(d => d.dataset.fold)),
  };
}

// Reload, Back and a link to a section. Every section is built after the
// fetch, so the browser's own scroll restoration and a #exp-... fragment find
// no element when they look. The page keeps the place itself: on pagehide it
// saves what readPlace() reads, and after the first render it scrolls to the
// fragment's section, or else back to the saved place. A page left before its
// sections arrived has no place of its own and keeps the one already saved.
function savePlace() {
  if (!state.payload) return;
  const { id, offset } = readPlace();
  try { sessionStorage.setItem(PLACE_KEY, JSON.stringify({ id, offset })); } catch (e) { /* a place is a convenience */ }
}
function takePlace() {
  let saved = null;
  try {
    saved = JSON.parse(sessionStorage.getItem(PLACE_KEY));
    sessionStorage.removeItem(PLACE_KEY);
  } catch (e) { saved = null; }
  return saved && typeof saved.id === 'string' && Number.isFinite(saved.offset) ? saved : null;
}
function fragmentTarget() {
  try {
    const id = decodeURIComponent(location.hash.slice(1));
    return id ? document.getElementById(id) : null;
  } catch (e) { return null; }
}
function restorePlace() {
  const target = fragmentTarget();
  const saved = takePlace();
  if (target) target.scrollIntoView();
  else {
    const anchor = saved ? $(saved.id) : null;
    if (anchor) window.scrollBy(0, anchor.getBoundingClientRect().top - saved.offset);
  }
  // From here every section exists, so the browser's own restoration is right
  // again: Back after a summary link returns to where the reader was.
  try { history.scrollRestoration = 'auto'; } catch (e) { /* the browser keeps its own mode */ }
}

function render() {
  const place = readPlace();
  mounter.clear();
  renderError();
  renderBuilt();
  renderSummary();
  const charts = renderSections();
  renderNotRead();
  for (const fold of document.querySelectorAll('details[data-fold]')) {
    if (place.open.has(fold.dataset.fold)) fold.open = true;
  }
  // Mounted once the whole page is built: each host has its width, and no
  // layout is read while the page is shorter than before, so the browser has
  // no shorter page to clamp the scroll to. Then the reader's section goes
  // back to its offset.
  for (const chart of charts) mounter.mount(chart.host, chart.draw);
  const anchor = place.id ? $(place.id) : null;
  if (anchor) window.scrollBy(0, anchor.getBoundingClientRect().top - place.offset);
}

// ---------------------------------------------------- theme and language
// Presentation only: switching either never changes a value on this page.
function syncThemeButton() {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
  const button = $('theme-toggle');
  if (!button) return;
  button.title = t(currentLang, theme === 'dark' ? 'theme.to_light' : 'theme.to_dark');
  button.setAttribute('aria-pressed', String(theme === 'dark'));
  button.querySelector('use')?.setAttribute('href', theme === 'dark' ? '#i-sun' : '#i-moon');
}

function applyTheme(name) {
  const theme = THEMES.includes(name) ? name : 'light';
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content',
      getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4f3ed');
  }
  syncThemeButton();
  remember(STORE.theme, theme);
}

function applyLanguage(name) {
  currentLang = resolveLang(name);
  applyTranslations(document, currentLang);
  const button = $('lang-toggle');
  if (button) {
    const other = currentLang === 'ar' ? 'en' : 'ar';
    button.title = t(currentLang, other === 'en' ? 'lang.switch_to_english' : 'lang.switch_to_arabic');
    setText(button.querySelector('span'), other === 'en' ? 'EN' : 'AR');
  }
  syncThemeButton();
  render();
  remember(STORE.lang, currentLang);
}

// ---------------------------------------------------------------- boot
async function load() {
  let response;
  try {
    response = await fetch('/api/results', { cache: 'no-store' });
  } catch (err) {
    state.failure = err?.name || 'Error';
    render();
    return;
  }
  if (response.status !== 200) {
    state.failure = await failureOf(response);
    render();
    return;
  }
  state.payload = await response.json();
  render();
  restorePlace();
}

// A failed build answers `results failed: <Type>` (app/results_api.py): the
// page names the status and that type, and nothing else of the body.
async function failureOf(response) {
  const status = String(response.status);
  try {
    const detail = (await response.json())?.detail;
    const m = typeof detail === 'string' ? /^results failed: ([A-Za-z_][A-Za-z0-9_]*)$/.exec(detail) : null;
    return m ? `${status} ${m[1]}` : status;
  } catch (e) { return status; }
}

function start() {
  try { history.scrollRestoration = 'manual'; } catch (e) { /* the page restores the place itself either way */ }
  window.addEventListener('pagehide', savePlace);
  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });
  applyTheme(recall(STORE.theme, THEMES,
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  load().catch(err => {
    console.error(err);
    state.failure = err?.name || 'Error';
    render();
  });
}

start();

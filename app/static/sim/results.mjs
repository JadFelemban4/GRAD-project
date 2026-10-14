// The results tab (/results): fetch, render, language, theme.
//
// PRESENTATION ONLY. The server publishes stable result snapshots and sends
// values; results-view.mjs chooses each sentence and
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
import { t, STRINGS, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { createArtifactSync } from './artifact-sync.mjs';
import { itemView, statusView } from './artifact-view.mjs';
import { inline } from './results-format.mjs?v=R1a';
import { createMounter } from './charts-lib.mjs?v=R1a';
import {
  ROLE_VAR, HAND_ROLES, pairsLayout, handLayout, pairsTable, handTable, drawPairs, drawHand,
} from './results-charts.mjs?v=R1a';
import {
  sectionName, nameSlot, metaText, plantView, verdictView, noteItems, summaryRows, unavailableText,
  notReadItems, builtView, checkItems, unpairedItems, thermalNote, meiLines,
} from './results-view.mjs?v=R1a';
import { parseSelectionHash, resolveChoice, selectedSections, selectionHash } from './results-selector.mjs?v=R1a';
import { createGraphicsBrowser } from './graphics-browser.mjs?v=R1a';
import { graphicsText } from './graphics-strings.mjs?v=R1a';

const $ = id => document.getElementById(id);
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };
const PLACE_KEY = 'grad.results.place';
const ARMS = ['sighted', 'blind'];

let currentLang = DEFAULT_LANG;
let pageActive = true;
let bootController = null;
const state = {
  payload: null,   // GET /api/results, once it has arrived
  failure: null,   // what to put in {status} when it did not
  artifactStatus: null,
  primaryChoice: '',
  compareChoice: '',
  compareEnabled: false,
  selectionInitialized: false,
};
const mounter = createMounter({ onError: chartFailed });
const sectionNodes = new Map();
const registryNodes = new Map();
const artifactNodes = new Map();
let summarySignature = null;
let graphicsBrowser = null;

function registrySets() {
  return (state.payload?.artifacts?.items || []).filter(item => item.kind === 'agent_set');
}
function choices() {
  const evaluations = (state.payload?.sections || []).map(section => ({
    id: section.id, type: 'evaluation', label: sectionName(section, currentLang), section,
    ready: section.state === 'ok',
  }));
  const sets = registrySets().map(item => ({
    id: `set:${item.id}`, type: 'agent_set',
    label: `${item.name || item.relative_path || item.id}${['current', 'updating / last valid snapshot'].includes(item.coherence)
      ? '' : ` · ${t(currentLang, 'results.selector.set_pending')}`}`,
    ready: ['current', 'updating / last valid snapshot'].includes(item.coherence), item,
  }));
  const reference = state.payload?.graphics?.reference_panels?.length
    ? [{id:'reference',type:'reference',label:graphicsText(currentLang,'reference'),ready:true}] : [];
  return [...evaluations, ...sets, ...reference];
}
function initialChoice(all) {
  return all.find(choice => choice.type === 'evaluation' && choice.section?.state === 'ok')
    || all.find(choice => choice.type === 'evaluation')
    || all.find(choice => choice.type === 'agent_set' && choice.ready)
    || (state.payload?.updating ? null : all[0])
    || null;
}
function selectedChoice() {
  return choices().find(choice => choice.id === state.primaryChoice) || null;
}
function chosenSections() {
  const sections = state.payload?.sections || [];
  const compareId = state.compareEnabled && selectedChoice()?.type === 'evaluation' ? state.compareChoice : '';
  return selectedSections(sections, state.primaryChoice, compareId);
}
function writeSelectionHash(mode = 'replace') {
  if (!state.selectionInitialized || !state.primaryChoice) return;
  const next = selectionHash(state.primaryChoice,
    state.compareEnabled ? state.compareChoice : '', choices());
  if (!next || location.hash === next) return;
  try { history[`${mode}State`](null, '', next); }
  catch (e) { location.hash = next; }
}
function applySelectionHash() {
  // Resolve browser navigation through the same readiness gate as first load.
  state.primaryChoice = '';
  state.compareChoice = '';
  state.compareEnabled = false;
  state.selectionInitialized = false;
  render();
  writeSelectionHash('replace');
  const choice = selectedChoice();
  const targetId = choice?.type === 'agent_set' ? 'registry-selection' : state.primaryChoice;
  $(targetId)?.scrollIntoView?.({ block: 'start' });
}

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
function syncSelect(select, entries, selected) {
  if (!select) return;
  const signature = JSON.stringify(entries.map(entry => [entry.value, entry.label]));
  if (select.dataset.optionSignature !== signature) {
    select.textContent = '';
    for (const entry of entries) {
      const option = el('option', '', entry.label);
      option.value = entry.value;
      select.appendChild(option);
    }
    select.dataset.optionSignature = signature;
  }
  select.value = entries.some(entry => entry.value === selected) ? selected : (entries[0]?.value || '');
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

function renderSelectors() {
  const box = $('experiment-controls');
  const primary = $('experiment-select');
  const compareToggle = $('compare-enabled');
  const compareControl = $('compare-control');
  const compareField = $('compare-field');
  const compare = $('compare-select');
  if (!box || !primary || !state.payload) return;
  const all = choices();
  if (!state.selectionInitialized) {
    const parsed = parseSelectionHash(location.hash || '', all);
    if (parsed) {
      state.primaryChoice = parsed.primary;
      state.compareChoice = parsed.compare;
      state.compareEnabled = parsed.compareEnabled;
      state.selectionInitialized = true;
    } else if (!location.hash || !state.payload.updating) {
      // An explicit link may reference results absent from a partial snapshot.
      // Keep it pending until it resolves, the snapshot settles, or the reader chooses.
      const initial = initialChoice(all);
      if (initial) {
        state.primaryChoice = initial.id;
        state.selectionInitialized = true;
      }
    }
  }
  if (state.selectionInitialized) state.primaryChoice = resolveChoice(all, state.primaryChoice, location.hash || '');
  const choice = all.find(item => item.id === state.primaryChoice);
  if (choice?.type !== 'evaluation') {
    state.compareEnabled = false;
    state.compareChoice = '';
  }
  const evaluations = all.filter(item => item.type === 'evaluation');
  const primaryEntries = [
    ...(!state.primaryChoice ? [{ value: '', label: t(currentLang, 'results.selector.waiting') }] : []),
    ...all.map(item => ({ value: item.id, label: item.label })),
  ];
  const compareEntries = [{ value: '', label: t(currentLang, 'results.selector.choose_second') },
    ...evaluations.filter(item => item.id !== state.primaryChoice).map(item => ({ value: item.id, label: item.label }))];
  syncSelect(primary, primaryEntries, state.primaryChoice);
  state.compareChoice = compareEntries.some(entry => entry.value === state.compareChoice) ? state.compareChoice : '';
  syncSelect(compare, compareEntries, state.compareChoice);
  compareToggle.checked = state.compareEnabled;
  compareToggle.disabled = !evaluations.length || choice?.type !== 'evaluation';
  compareControl.hidden = evaluations.length < 2 || choice?.type !== 'evaluation';
  compareField.hidden = !state.compareEnabled || choice?.type !== 'evaluation';
  box.hidden = all.length === 0;
  writeSelectionHash('replace');
}

function renderSummary() {
  const rows = $('summary-rows');
  const summary = $('summary');
  if (!rows || !summary) return;
  const selected = chosenSections();
  const selectedIds = selected.map(section => section.id);
  const signature = JSON.stringify([currentLang, selectedIds,
    state.payload && summaryRows({ ...state.payload, sections: selected }, currentLang)]);
  if (signature === summarySignature) return;
  summarySignature = signature;
  rows.textContent = '';
  if (!state.payload || !selectedIds.length) { summary.hidden = true; return; }
  for (const row of summaryRows({ ...state.payload, sections: selected }, currentLang)) {
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
  const prefixes = new Set(chosenSections().map(section => section.prefix));
  const raw = (state.payload?.not_read || []).filter(item => {
    const match = /(?:^|\/)([a-z][a-z0-9]*(?:_[a-z0-9]+)*)_seed\d+\.txt$/i.exec(item.path || '');
    return match && prefixes.has(match[1]);
  });
  const items = state.payload ? notReadItems(raw, currentLang) : [];
  for (const item of items) {
    const li = el('li');
    const path = el('code', '', item.path);
    path.dir = 'ltr';
    li.append(path, el('span', '', item.reason));
    ul.appendChild(li);
  }
  box.hidden = items.length === 0;
}

function evidenceText(name, available) {
  const evidenceKey = `artifact.evidence.${name}`;
  const evidenceName = STRINGS[currentLang][evidenceKey]
    ? t(currentLang, evidenceKey) : inline(currentLang, name);
  return t(currentLang, available ? 'artifact.evidence.available' : 'artifact.evidence.unavailable', { name: evidenceName });
}

function lifecycleText(lifecycle) {
  const value = ['running', 'finalizing', 'finished', 'interrupted', 'unknown'].includes(lifecycle)
    ? lifecycle : 'unknown';
  return t(currentLang, value === 'finished' ? 'artifact.lifecycle.published' : `artifact.lifecycle.${value}`);
}

function metricText(name) {
  const key = `results.registry.metric.${name}`;
  return STRINGS[currentLang][key]
    ? t(currentLang, key) : t(currentLang, 'results.registry.metric.other', { name: inline(currentLang, name) });
}

function statisticText(name) {
  const key = `results.registry.stat.${name}`;
  return STRINGS[currentLang][key]
    ? t(currentLang, key) : t(currentLang, 'results.registry.stat.other', { name: inline(currentLang, name) });
}

function summaryTable(summary) {
  if (!summary || typeof summary !== 'object' || Array.isArray(summary) || !Object.keys(summary).length) {
    return el('p', 'rc-registry-unavailable', t(currentLang, 'results.registry.summary.unavailable'));
  }
  const table = el('table', 'rc-registry-table');
  const caption = el('caption', '', t(currentLang, 'results.registry.summary.caption'));
  const head = el('tr');
  for (const key of ['results.registry.summary.metric', 'results.registry.summary.statistic', 'results.registry.summary.value']) {
    head.appendChild(el('th', '', t(currentLang, key)));
  }
  const thead = el('thead');
  thead.appendChild(head);
  const tbody = el('tbody');
  for (const [metric, raw] of Object.entries(summary)) {
    const values = raw && typeof raw === 'object' && !Array.isArray(raw)
      ? Object.entries(raw) : [['value', raw]];
    if (!values.length) values.push(['value', null]);
    for (const [statistic, value] of values) {
      const tr = el('tr');
      tr.append(el('th', '', metricText(metric)), el('td', '', statisticText(statistic)));
      tr.appendChild(el('td', 'rc-registry-value', value === null || value === undefined
        ? t(currentLang, 'results.registry.summary.unavailable')
        : inline(currentLang, typeof value === 'string' ? value : String(value))));
      tbody.appendChild(tr);
    }
  }
  table.append(caption, thead, tbody);
  return table;
}

function capabilityList(capabilities, className) {
  const ul = el('ul', className);
  for (const [name, available] of Object.entries(capabilities || {})) {
    ul.appendChild(el('li', '', evidenceText(name, available === true)));
  }
  return ul;
}

function renderRegistrySet(item) {
  const node = el('article', 'rc-section rc-registry');
  node.id = 'registry-selection';
  const label = item.name || item.relative_path?.split('/').filter(Boolean).at(-1) || item.id;
  node.append(el('h2', '', label), el('p', 'rc-note', t(currentLang, 'results.registry.notice')));
  const ready = ['current', 'updating / last valid snapshot'].includes(item.coherence);
  if (item.coherence === 'updating / last valid snapshot') {
    node.appendChild(el('p', 'rc-note rc-registry-last-valid', t(currentLang, 'artifact.last_valid')));
  } else if (!ready) {
    node.appendChild(el('p', 'rc-note rc-registry-unavailable', t(currentLang, 'results.registry.pending')));
  }
  node.appendChild(el('h3', 'rc-registry-heading', t(currentLang, 'results.registry.capabilities')));
  node.appendChild(capabilityList(item.capabilities, 'rc-registry-capabilities'));
  const members = Array.isArray(item.members) ? item.members : [];
  node.appendChild(el('h3', 'rc-registry-heading', t(currentLang, 'results.registry.members')));
  if (!members.length && ready) node.appendChild(el('p', 'rc-registry-unavailable', t(currentLang, 'results.registry.members.empty')));
  const listNode = el('ul', 'rc-registry-members');
  for (const member of members) {
    const li = el('li');
    li.appendChild(el('strong', '', member.name || member.relative_path?.split('/').filter(Boolean).at(-1) || ''));
    li.append(el('span', 'rc-registry-status', `${t(currentLang, 'results.registry.member.lifecycle')}: ${lifecycleText(member.lifecycle)}`));
    li.appendChild(capabilityList(member.capabilities, 'rc-registry-member-capabilities'));
    const details = el('details', 'rc-registry-summary');
    details.dataset.fold = `registry:${item.id}:${member.name || member.relative_path || ''}`;
    details.appendChild(el('summary', '', t(currentLang, 'results.registry.member.summary')));
    details.appendChild(summaryTable(member.summary));
    li.appendChild(details);
    listNode.appendChild(li);
  }
  node.appendChild(listNode);
  return node;
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

// Reuse unchanged sections, including their mounted charts and open folds.
function renderSections() {
  const host = $('sections');
  if (!host) return [];
  const allSections = state.payload?.sections || [];
  const charts = [];
  for (const [id, previous] of sectionNodes) {
    if (allSections.some(section => section.id === id)) continue;
    for (const chart of previous.charts) {
      if (!chart.mounted) continue;
      mounter.unmount(chart.host);
      chart.mounted = false;
    }
    previous.node.remove();
    sectionNodes.delete(id);
  }
  const currentSets = new Set(registrySets().map(item => `set:${item.id}`));
  for (const [id, previous] of registryNodes) {
    if (currentSets.has(id)) continue;
    previous.node.remove();
    registryNodes.delete(id);
  }
  const choice = selectedChoice();
  if (choice?.type === 'agent_set') {
    for (const [id, previous] of registryNodes) {
      if (id !== choice.id) previous.node.remove();
    }
    for (const previous of sectionNodes.values()) {
      previous.node.remove();
      for (const chart of previous.charts) {
        if (!chart.mounted) continue;
        mounter.unmount(chart.host);
        chart.mounted = false;
      }
    }
    const signature = JSON.stringify([currentLang, choice.item]);
    let built = registryNodes.get(choice.id);
    if (built?.signature !== signature) {
      built?.node.remove();
      built = { node: renderRegistrySet(choice.item), signature };
      registryNodes.set(choice.id, built);
    }
    if (host.children[0] !== built.node) host.insertBefore(built.node, host.children[0] || null);
    return charts;
  }
  for (const previous of registryNodes.values()) previous.node.remove();
  const sections = chosenSections();
  const rows = summaryRows({ ...state.payload, sections }, currentLang);
  const selectedIds = new Set(sections.map(section => section.id));
  for (const [id, previous] of sectionNodes) {
    if (selectedIds.has(id)) continue;
    previous.node.remove();
    for (const chart of previous.charts) {
      if (!chart.mounted) continue;
      mounter.unmount(chart.host);
      chart.mounted = false;
    }
  }
  for (const [index, section] of sections.entries()) {
    const markers = rows.find(r => r.id === section.id)?.markers || [];
    const signature = JSON.stringify([currentLang, section, markers]);
    let built = sectionNodes.get(section.id);
    if (built?.signature !== signature) {
      if (built) {
        for (const chart of built.charts) {
          if (!chart.mounted) continue;
          mounter.unmount(chart.host);
          chart.mounted = false;
        }
        built.node.remove();
      }
      built = { ...buildSection(section, markers), signature };
      sectionNodes.set(section.id, built);
    }
    charts.push(...built.charts.filter(chart => !chart.mounted));
    if (host.children[index] !== built.node) host.insertBefore(built.node, host.children[index] || null);
  }
  return charts;
}

function renderArtifactStrip() {
  const status = statusView({ ...(state.payload?.artifacts || {}), ...(state.artifactStatus || {}) }, currentLang);
  setText($('artifact-status'), `${status.connection} · ${status.lastSuccess}${state.payload?.artifacts?.restart_needed ? ` · ${status.restartNeeded}` : ''}`);
  const host = $('artifact-list');
  if (!host) return;
  const allItems = state.payload?.artifacts?.items || [];
  const choice = selectedChoice();
  let items = [];
  if (choice?.type === 'agent_set') {
    items = allItems.filter(item => item.id === choice.item.id);
  } else {
    const prefixes = new Set(chosenSections().map(section => section.prefix));
    items = allItems.filter(item => {
      if (item.kind !== 'evaluation_text') return false;
      const path = item.relative_path || '';
      const match = /(?:^|\/)([a-z][a-z0-9]*(?:_[a-z0-9]+)*)_seed\d+\.txt$/i.exec(path);
      return match && prefixes.has(match[1]);
    });
  }
  for (const [id, previous] of artifactNodes) {
    if (items.some(item => item.id === id)) continue;
    previous.node.remove();
    artifactNodes.delete(id);
  }
  for (const item of items) {
    const signature = JSON.stringify([currentLang, item]);
    const previous = artifactNodes.get(item.id);
    if (previous?.signature === signature) continue;
    const view = itemView(item, currentLang);
    if (item.kind === 'agent_set') {
      view.availability = view.availability.replace(` · ${t(currentLang, 'artifact.reader.pending')}`, '');
    }
    const node = previous?.node || el('details', 'artifact-item');
    const open = node.open;
    node.textContent = '';
    const summary = el('summary');
    const path = el('bdi', '', item.relative_path);
    path.setAttribute('dir', 'ltr');
    summary.append(path, el('span', '', ` · ${view.lifecycle}`));
    node.appendChild(summary);
    for (const line of [view.source, view.availability, view.compatibility, view.issues]) node.appendChild(el('p', '', line));
    if (item.coherence === 'updating / last valid snapshot') node.appendChild(el('p', '', t(currentLang, 'artifact.last_valid')));
    node.open = open;
    if (!previous) host.appendChild(node);
    artifactNodes.set(item.id, { node, signature });
  }
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
  const parsed = parseSelectionHash(location.hash || '', choices());
  if (parsed) {
    const choice = choices().find(item => item.id === parsed.primary);
    return document.getElementById(choice?.type === 'agent_set' ? 'registry-selection' : parsed.primary);
  }
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
  const focus = document.activeElement;
  const focusId = focus?.id;
  const focusFold = focus?.closest?.('details[data-fold]')?.dataset.fold;
  renderError();
  renderBuilt();
  renderSelectors();
  renderSummary();
  const charts = renderSections();
  renderGraphics();
  renderNotRead();
  renderArtifactStrip();
  for (const fold of document.querySelectorAll('details[data-fold]')) {
    if (place.open.has(fold.dataset.fold)) fold.open = true;
  }
  // Mounted once the whole page is built: each host has its width, and no
  // layout is read while the page is shorter than before, so the browser has
  // no shorter page to clamp the scroll to. Then the reader's section goes
  // back to its offset.
  for (const chart of charts) {
    mounter.mount(chart.host, chart.draw);
    chart.mounted = true;
  }
  if (focus && (document.activeElement !== focus || !focus.parentNode)) {
    const replacement = focusId ? $(focusId) : focusFold
      ? [...document.querySelectorAll('details[data-fold]')].find(d => d.dataset.fold === focusFold)?.querySelector('summary') : null;
    (replacement || $('experiment-select'))?.focus({ preventScroll: true });
  }
  const anchor = place.id ? $(place.id) : null;
  if (anchor) window.scrollBy(0, anchor.getBoundingClientRect().top - place.offset);
}

function renderGraphics() {
  const host=$('graphics');
  if(!host)return;
  graphicsBrowser ||= createGraphicsBrowser(host,{onGroup:group=>{
    const sectionHost=$('sections');
    if(sectionHost)sectionHost.hidden=selectedChoice()?.type==='evaluation' && group!=='evaluation';
  }});
  const choice=selectedChoice(),graphics=state.payload?.graphics;
  let panels=[],recorderTest=false;
  if(choice?.type==='reference')panels=graphics?.reference_panels || [];
  if(choice?.type==='agent_set'){
    const set=graphics?.agent_sets?.find(s=>s.relative_path===choice.item.relative_path);
    panels=(set?.panels || []).map(panel=>({...panel,provenance:panel.provenance || set.provenance,issues:set.issues}));recorderTest=Boolean(set?.recorder_test);
  }
  if(choice?.type==='evaluation')panels=graphics?.experiment_panels?.[choice.section.prefix] || [];
  graphicsBrowser.render({sourceKey:choice?.id || '',title:choice?.label || '',panels,lang:currentLang,
    updating:Boolean(state.payload?.updating),recorderTest,
    externalGroups:choice?.type==='evaluation'?{evaluation:Math.max(1,$('sections')?.children.length || 0)}:{}});
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
async function load({ refresh = false, signal } = {}) {
  if (!refresh && !signal) {
    bootController?.abort();
    bootController = new AbortController();
    signal = bootController.signal;
  }
  let response;
  try {
    response = await fetch('/api/results', { cache: 'no-store', signal });
  } catch (err) {
    if (signal?.aborted || !pageActive) return;
    if (refresh) throw err;
    state.failure = err?.name || 'Error';
    render();
    return;
  }
  if (signal?.aborted || !pageActive) return;
  if (response.status !== 200) {
    if (refresh) throw new Error(`HTTP ${response.status}`);
    state.failure = await failureOf(response);
    render();
    return;
  }
  const body = await response.json();
  if (signal?.aborted || !pageActive) return;
  if (!Array.isArray(body?.sections)) throw new Error('invalid results snapshot');
  state.failure = null;
  state.payload = body;
  render();
  if (!refresh) restorePlace();
  if (body.artifacts) artifactSync.start();
}

const artifactSync = createArtifactSync({
  readRevision: async signal => {
    const response = await fetch('/api/artifacts/revision', { cache: 'no-store', signal });
    if (response.status !== 200) throw new Error(`HTTP ${response.status}`);
    const next = await response.json();
    if (typeof next?.revision !== 'string') throw new Error('invalid artifact revision');
    // A file may change while the reader builds, before a new revision settles.
    return { ...next, updating: Boolean(next.updating || state.payload?.updating) };
  },
  onChange: async (_previous, next, { signal }) => {
    const old = state.payload?.artifacts;
    state.artifactStatus = { ...state.artifactStatus, ...next };
    if (!old || state.payload.updating || ['results_revision', 'plant_revision', 'results_updating']
      .some(key => old[key] !== next[key])) await load({ refresh: true, signal });
  },
  onStatus: value => { state.artifactStatus = { ...state.artifactStatus, ...value }; renderArtifactStrip(); },
});

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
  window.addEventListener('pagehide', () => {
    pageActive = false;
    savePlace();
    bootController?.abort();
    artifactSync.stop();
  });
  window.addEventListener('pageshow', () => {
    if (pageActive) return;
    pageActive = true;
    if (state.payload?.artifacts) artifactSync.start();
    else load().catch(err => console.error(err));
  });
  document.addEventListener('visibilitychange', () => artifactSync.visibilityChanged());
  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });
  $('experiment-select')?.addEventListener('change', () => {
    state.primaryChoice = $('experiment-select').value;
    state.compareChoice = state.compareChoice === state.primaryChoice ? '' : state.compareChoice;
    state.selectionInitialized = true;
    writeSelectionHash('push');
    render();
  });
  $('compare-enabled')?.addEventListener('change', () => {
    state.compareEnabled = Boolean($('compare-enabled').checked);
    if (!state.compareEnabled) state.compareChoice = '';
    writeSelectionHash('push');
    render();
  });
  $('compare-select')?.addEventListener('change', () => {
    state.compareChoice = $('compare-select').value;
    writeSelectionHash('push');
    render();
  });
  window.addEventListener('hashchange', applySelectionHash);
  window.addEventListener('popstate', applySelectionHash);
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

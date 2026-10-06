// The results tab's view helpers (/results): what each line of a section
// says, in Arabic or English, from the values GET /api/results sent.
//
// PURE: no DOM, no fetch, no physics, and no statistic. Every number here is
// a value the server read from a file; this module only chooses the string
// (results-strings.mjs) and formats the values put into it. results.mjs owns
// the DOM and calls these.
//
// Two rules, pinned by results-view.test.mjs:
//  - Every value that lands inside a sentence (a number, hash, commit, file
//    path, date, module or Python version) goes through inline(), so in
//    Arabic it sits in a left-to-right isolate and keeps its order.
//  - A state or key this module does not know is never dressed up as a known
//    one: an unknown plant state reads "cannot compare", an unknown check or
//    file reason is shown as its own words, and a note without a string shows
//    its key, so the gap is visible.
import { t } from './i18n.mjs';
import { EM_DASH, MINUS, fmtInt, inline } from './results-format.mjs?v=R1a';

const PLANT_STATES = ['forced', 'not_recorded', 'another', 'cannot_compare', 'same_code', 'same', 'mixed'];
const ARMS = ['sighted', 'blind'];

// t() returns the key itself when no language has it.
const known = (lang, key) => t(lang, key) !== key;

// A recorded number as the file wrote it: integers whole and grouped, other
// numbers as they came (0.2 stays 0.2, 1.0 reads 1), the minus as U+2212.
function numText(v) {
  if (typeof v !== 'number' || !Number.isFinite(v)) return EM_DASH;
  if (Number.isInteger(v)) return fmtInt(v);
  return String(v).replace('-', MINUS);
}

// Any value bound for a {placeholder}: formatted, then isolated in Arabic.
function slot(lang, v) {
  if (v === null || v === undefined || v === '') return inline(lang, EM_DASH);
  return inline(lang, typeof v === 'number' ? numText(v) : String(v));
}

function slots(lang, values) {
  const out = {};
  for (const [k, v] of Object.entries(values || {})) out[k] = slot(lang, v);
  return out;
}

/** The section's heading: run_phase_d's name, or the prefix said to have none. */
export function sectionName(section, lang) {
  if (section && typeof section.name === 'string' && section.name) return section.name;
  return t(lang, 'results.section.no_name', { prefix: slot(lang, section?.prefix) });
}

/**
 * The section's name for a sentence's bare {name} or {other} slot: a recorded
 * name is Latin and goes in an isolate; the "no name recorded" line already
 * isolates its prefix and is Arabic in Arabic, so it goes in as it is.
 */
export function nameSlot(section, lang) {
  if (section && typeof section.name === 'string' && section.name) return slot(lang, section.name);
  return sectionName(section, lang);
}

/** "20 frozen episodes · frozen 22 Sep 2026 · protocol d2", from the header. */
export function metaText(section, lang) {
  return t(lang, 'results.section.meta', {
    episodes: slot(lang, section?.episodes),
    frozen: slot(lang, section?.frozen),
    protocol: slot(lang, section?.protocol),
  });
}

function stateText(state, lang) {
  return t(lang, `results.plant.${PLANT_STATES.includes(state) ? state : 'cannot_compare'}`);
}

function reasonText(reason, recordedPython, livePython, lang) {
  const key = `results.plant.reason.${reason}`;
  if (!known(lang, key)) return slot(lang, reason);
  return t(lang, key, { recorded: slot(lang, recordedPython), live: slot(lang, livePython) });
}

const distinct = values => [...new Set(values.filter(v => v !== null && v !== undefined && v !== ''))];

/**
 * The plant line of a section and its details, from section_provenance's
 * answer: {state, reason, tag, commits, files: {seed: classify_eval(...)}}.
 * A common state lists both hashes, the tag, the git route, the reason, the
 * recorded commits and each file's own commit; "mixed" lists every seed.
 */
export function plantView(prov, lang) {
  const files = Object.entries(prov?.files || {})
    .sort((a, b) => Number(a[0]) - Number(b[0])).map(([seed, f]) => ({ seed, ...f }));
  const state = prov?.state || 'cannot_compare';
  const details = [];
  if (state === 'mixed') {
    for (const f of files) {
      const parts = [t(lang, 'results.tip.seed', { seed: slot(lang, Number(f.seed)) }), stateText(f.state, lang)];
      if (f.reason) parts.push(reasonText(f.reason, f.recorded?.python, f.live?.python, lang));
      details.push(parts.join(' · '));
    }
    return { state, text: stateText(state, lang), details };
  }
  const forced = distinct(files.flatMap(f => f.forced || []));
  if (state === 'forced' && forced.length) {
    details.push(t(lang, 'results.plant.forced_lines'));
    for (const line of forced) details.push(slot(lang, line));
  }
  const recorded = distinct(files.map(f => f.recorded?.plant_sha));
  const live = distinct(files.map(f => f.live?.plant_sha));
  if (recorded.length && state !== 'forced' && state !== 'not_recorded') {
    details.push(t(lang, 'results.plant.hashes', { recorded: slot(lang, recorded.join(', ')), live: slot(lang, live.join(', ')) }));
  }
  if (prov?.tag) details.push(t(lang, 'results.plant.tag', { tag: slot(lang, prov.tag) }));
  if (files.length && files.every(f => f.route === 'git')) details.push(t(lang, 'results.plant.route_git'));
  if (prov?.reason) {
    details.push(reasonText(prov.reason, distinct(files.map(f => f.recorded?.python)).join(', '),
      distinct(files.map(f => f.live?.python)).join(', '), lang));
  }
  if ((prov?.commits || []).length) details.push(t(lang, 'results.plant.commits', { list: slot(lang, prov.commits.join(', ')) }));
  const committed = new Map();
  for (const f of files) {
    const c = f.file?.commit;
    if (f.file?.changed) {
      details.push(`${slot(lang, f.file.rel)}: ${t(lang, 'results.plant.changed', { date: slot(lang, c?.date) })}`);
    } else if (c && c.short) {
      committed.set(`${c.short} ${c.date}`, c);
    }
  }
  for (const c of committed.values()) {
    details.push(t(lang, 'results.plant.committed', { commit: slot(lang, c.short), date: slot(lang, c.date) }));
  }
  return { state, text: stateText(state, lang), details };
}

/**
 * The verdict block, from app.agent_catalog.verdict as the server passed it.
 * 'none' gets this tab's own line, never the catalog's NONE_TEXT (the server
 * already sends its short as null); a verdict the build could not import is
 * 'unavailable'. Each quoted line is cited results/<file>:<line>, a range when
 * the quote holds several lines, as /agents cites them.
 */
export function verdictView(verdict, lang) {
  const state = verdict?.state || 'unavailable';
  let short;
  if (state === 'unavailable') short = t(lang, 'results.verdict.unavailable');
  else if (state === 'none') short = t(lang, 'results.verdict.none');
  else short = verdict?.short?.[lang] || EM_DASH;
  const cells = (verdict?.cells || []).map(c => ({ cell: String(c.cell), gloss: c.gloss?.[lang] || '' }));
  const lines = (verdict?.lines || []).map(l => {
    const n = String(l.text).split('\n').length;
    const where = n > 1 ? `${l.line}-${l.line + n - 1}` : String(l.line);
    return { cite: `results/${l.file}:${where}`, text: String(l.text) };
  });
  return { state, short, cells, lines };
}

/** The required notes, in the server's order, each with its values filled. */
export function noteItems(notes, lang) {
  return (notes || []).map(n => t(lang, `results.note.${n.key}`, slots(lang, n.values)));
}

/**
 * One row per section, in the server's order: name, plant state, short
 * verdict only, and the "continues" mark. A section that could not be built
 * shows why in the verdict column and claims no plant state.
 */
export function summaryRows(payload, lang) {
  const sections = payload?.sections || [];
  const nameOf = prefix => {
    const other = sections.find(s => s.prefix === prefix);
    return other ? nameSlot(other, lang) : slot(lang, prefix);
  };
  return sections.map(s => {
    if (s.state !== 'ok') {
      return { id: s.id, name: sectionName(s, lang), plant: EM_DASH, verdict: unavailableText(s.error, lang), markers: [] };
    }
    const v = verdictView(s.verdict, lang);
    return {
      id: s.id,
      name: sectionName(s, lang),
      plant: plantView(s.provenance, lang).text,
      verdict: v.state === 'none' ? t(lang, 'results.summary.no_verdict') : v.short,
      markers: s.continues ? [t(lang, 'results.summary.continues', { other: nameOf(s.continues) })] : [],
    };
  });
}

/** Why a section is not shown: a missing file names its command; nothing else does. */
export function unavailableText(error, lang) {
  const e = error || {};
  switch (e.kind) {
    case 'missing':
      return t(lang, 'results.section.unavailable.missing', { file: slot(lang, e.file), command: slot(lang, e.command) });
    case 'read':
      return t(lang, 'results.section.unavailable.read', { file: slot(lang, e.file), type: slot(lang, e.type) });
    case 'module':
      return t(lang, 'results.section.unavailable.module', { module: slot(lang, e.module) });
    default:
      return t(lang, 'results.section.unavailable.build', { type: slot(lang, e.type) });
  }
}

/** Every file the build did not read, with the reason in words. */
export function notReadItems(notRead, lang) {
  return (notRead || []).map(item => {
    const key = `results.not_read.reason.${item.reason}`;
    return {
      path: String(item.path),
      reason: known(lang, key) ? t(lang, key, { type: slot(lang, item.type) }) : slot(lang, item.reason),
    };
  });
}

/** The line under the intro, and the warnings above the summary. */
export function builtView(built, failures, lang) {
  const b = built || {};
  const line = t(lang, 'results.built.line', { head: slot(lang, b.head), python: slot(lang, b.python), plant: slot(lang, b.plant_sha) });
  const warnings = [];
  if (b.git === 'unavailable') warnings.push(t(lang, 'results.built.git_unavailable'));
  if (b.restart_needed) warnings.push(t(lang, 'results.built.restart'));
  if (b.derived_loaded_differs) warnings.push(t(lang, 'results.built.derived_restart'));
  for (const f of failures || []) {
    warnings.push(t(lang, 'results.import_failure', { module: slot(lang, f.module), type: slot(lang, f.type) }));
  }
  return { line, warnings };
}

/** Each cross-check's outcome; a check without a string is shown as its own words. */
export function checkItems(checks, lang) {
  return (checks || []).map(c => {
    const key = `results.check.${c.name}.${c.state}`;
    return known(lang, key) ? t(lang, key, { detail: slot(lang, c.detail) }) : slot(lang, `${c.name}: ${c.state}`);
  });
}

/** "Seed 3 has no pair (Sighted agent); it is not drawn." Arms only. */
export function unpairedItems(unpaired, lang) {
  const sep = lang === 'ar' ? '، ' : ', ';
  return (unpaired || []).map(u => {
    const have = (u.have || []).filter(r => ARMS.includes(r)).map(r => t(lang, `results.legend.${r}`));
    return t(lang, 'results.unpaired', { seed: slot(lang, u.seed), have: have.length ? have.join(sep) : EM_DASH });
  });
}

/** The thermal-only panel's note: null when every seed recorded it. */
export function thermalNote(section, lang) {
  if (section?.thermal_recorded === 'none') return t(lang, 'results.chart.thermal_none');
  if (section?.thermal_recorded !== 'some') return null;
  const seeds = (section.seeds || []).filter(s => s.thermal?.sighted && s.thermal?.blind).map(s => s.seed);
  return t(lang, 'results.chart.thermal_some', { seeds: slot(lang, seeds.join(', ')) });
}

/** What the MEI bracket is, and, where it applies, that it came after the result. */
export function meiLines(section, lang) {
  if (typeof section?.mei !== 'number' || !Number.isFinite(section.mei)) return [];
  const out = [t(lang, 'results.chart.mei', { mei: slot(lang, section.mei) })];
  if (section.mei_after_result) out.push(t(lang, 'results.chart.mei_after'));
  return out;
}

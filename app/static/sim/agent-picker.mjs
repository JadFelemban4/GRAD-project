// The three-select picker of /agents: experiment -> pair -> episode.
//
// PURE: no DOM, no fetch, no physics. It decides what may be chosen and how
// each choice reads, from the catalog the server sent (GET /api/agents/catalog,
// app/agent_api.py catalog()). It never computes a statistic or a difference
// between the two cars: the number on a pair is the results table's own row
// (analyse_phase_d2.load, rounded as the tables print it), and the page labels
// it "not this episode".
//
// HONESTY RULE: nothing is ever chosen for the viewer. With no address the page
// opens with nothing selected; an address selects only what exists in the
// catalog and can run, level by level, and nothing computes until «احسب».
// Every function here takes the catalog as an argument, so a node test can
// drive it from app/static/sim/agent-catalog.fixture.json.
import { t } from './i18n.mjs';

// The server's own patterns (app/agent_catalog.py RUNS_NAME, app/agent_api.py
// SEED_TEXT and EP_TEXT). Lowercase only: on Windows runs_C4 would open the
// runs_c4 directory under a name no verdict is recorded for.
const RUNS_RE = /^runs[a-z0-9_]*$/;
const SEED_RE = /^[0-9]{1,3}$/;
const EP_RE = /^[0-9]{1,2}$/;
const EP_MIN = 1;
const EP_MAX = 20;
const EM_DASH = '—';
// U+2066 LEFT-TO-RIGHT ISOLATE, U+2069 POP DIRECTIONAL ISOLATE and U+2212
// MINUS SIGN, written as escapes: all three are invisible or look like an ASCII
// character in an editor.
const LRI = '\u2066';
const PDI = '\u2069';
const MINUS = '\u2212';

export const NOTHING = Object.freeze({ runs: null, seed: null, ep: null });

/**
 * ?runs=&seed=&ep= read leniently, level by level: a level is kept only when
 * it matches the server's pattern AND every level above it was kept. Episodes
 * are 1..20. Nothing here says that a name exists; resolveSelection does.
 */
export function parsePickerQuery(search) {
  const q = new URLSearchParams(typeof search === 'string' ? search : '');
  const runs = q.get('runs');
  if (runs === null || !RUNS_RE.test(runs)) return { ...NOTHING };
  const seed = q.get('seed');
  if (seed === null || !SEED_RE.test(seed)) return { runs, seed: null, ep: null };
  const ep = q.get('ep');
  const n = ep !== null && EP_RE.test(ep) ? Number(ep) : null;
  return { runs, seed: Number(seed), ep: n !== null && n >= EP_MIN && n <= EP_MAX ? n : null };
}

/** The catalog's experiment for a runs directory name, or null. */
export function experimentOf(catalog, runs) {
  return (catalog?.experiments || []).find(e => e.runs === runs) || null;
}

/** True when at least one of the experiment's pairs may run; the select greys the others. */
export function selectable(experiment) {
  return Boolean(experiment) && (experiment.pairs || []).some(p => p.runnable);
}

/** The experiment's pair for a seed, or null. */
export function pairOf(experiment, seed) {
  return (experiment?.pairs || []).find(p => p.seed === seed) || null;
}

/** The frozen episodes a runnable pair is scored on, by its protocol; [] otherwise. */
export function episodesOf(catalog, pair) {
  if (!pair || !pair.runnable || !pair.protocol) return [];
  return catalog?.episodes?.[pair.protocol] || [];
}

/**
 * What an address may select in this catalog: an experiment only when it
 * exists and some pair of it can run, a seed only when that pair exists and
 * can run, an episode only when it is one of that pair's twenty. Everything
 * else is dropped, so a shared link can never select a refused pair.
 */
export function resolveSelection(catalog, query) {
  const exp = experimentOf(catalog, query?.runs ?? null);
  if (!selectable(exp)) return { ...NOTHING };
  const pair = pairOf(exp, query.seed);
  if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
  const ep = episodesOf(catalog, pair).find(e => e.idx === query.ep);
  return { runs: exp.runs, seed: pair.seed, ep: ep ? ep.idx : null };
}

/**
 * The selection after the viewer changes one select. `level` is 'runs',
 * 'seed' or 'ep'; `value` is the select's string value, '' for the
 * placeholder. A new experiment clears the pair and the episode (one that
 * cannot run clears everything); a new pair keeps the episode only when both
 * pairs are scored on the same protocol, so the same twenty episodes; anything
 * invalid clears its level and every level below it.
 */
export function choose(catalog, sel, level, value) {
  const current = { ...NOTHING, ...sel };
  if (level === 'runs') {
    const exp = experimentOf(catalog, value);
    return selectable(exp) ? { runs: exp.runs, seed: null, ep: null } : { ...NOTHING };
  }
  const exp = experimentOf(catalog, current.runs);
  if (!selectable(exp)) return { ...NOTHING };
  if (level === 'seed') {
    const pair = SEED_RE.test(String(value)) ? pairOf(exp, Number(value)) : null;
    if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
    const old = pairOf(exp, current.seed);
    const keep = current.ep !== null && Boolean(old) && old.protocol === pair.protocol;
    return { runs: exp.runs, seed: pair.seed, ep: keep ? current.ep : null };
  }
  if (level === 'ep') {
    const pair = pairOf(exp, current.seed);
    if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
    const ep = episodesOf(catalog, pair).find(e => String(e.idx) === String(value));
    return { runs: exp.runs, seed: pair.seed, ep: ep ? ep.idx : null };
  }
  return current;
}

/** The address for a selection: '' when nothing is selected, never more than what is. */
export function selectionSearch(sel) {
  if (!sel || sel.runs === null || sel.runs === undefined) return '';
  const q = new URLSearchParams({ runs: sel.runs });
  if (sel.seed !== null && sel.seed !== undefined) {
    q.set('seed', String(sel.seed));
    if (sel.ep !== null && sel.ep !== undefined) q.set('ep', String(sel.ep));
  }
  return `?${q}`;
}

/**
 * Can «احسب» be pressed? {ok, reason}: reason is null when ok, otherwise the
 * i18n key of what stops it. First the catalog still loading; then a missing
 * stable-baselines3, which no choice can cure, so it is the reason from the
 * moment the catalog arrives (design section 4, Runnability); then what is
 * still to choose, in the order the viewer chooses.
 */
export function computeState(catalog, sel) {
  if (!catalog) return { ok: false, reason: 'agents.pick.catalog_loading' };
  if (!catalog.sb3) return { ok: false, reason: 'agents.load.no_sb3' };
  const exp = experimentOf(catalog, sel?.runs ?? null);
  if (!exp) return { ok: false, reason: 'agents.pick.none' };
  const pair = pairOf(exp, sel.seed);
  if (!pair || !pair.runnable) return { ok: false, reason: 'agents.pick.need_pair' };
  if (!episodesOf(catalog, pair).some(e => e.idx === sel.ep)) {
    return { ok: false, reason: 'agents.pick.need_episode' };
  }
  return { ok: true, reason: null };
}

/**
 * `text` inside a left-to-right isolate, U+2066 ... U+2069. In an Arabic line
 * a bare "+360.6" is drawn "360.6+": the digits after Arabic letters become
 * Arabic numbers (UAX #9 W2) and the leading sign then resolves right-to-left.
 * The isolate keeps a signed number's sign on its left. formatDiff uses it for
 * the pair row, and agents.mjs for every signed number it puts into an
 * Arabic sentence (the held command, the models panel's choice and reversed
 * lines).
 */
export function isolateLtr(text) {
  return `${LRI}${text}${PDI}`;
}

/**
 * A results-table difference as the tables print it: signed, one decimal,
 * inside a left-to-right isolate (isolateLtr). U+2212 for a negative, as the
 * pause panel writes it; a value that rounds to 0.0 reads +0.0.
 */
export function formatDiff(v) {
  if (typeof v !== 'number' || !Number.isFinite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(1);
  const sign = v < 0 && text !== '0.0' ? MINUS : '+';
  return isolateLtr(`${sign}${text}`);
}

const fixed = (v, digits) => (typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : EM_DASH);
const percent = g => (typeof g === 'number' && Number.isFinite(g) ? (g * 100).toFixed(1) : EM_DASH);
const placeholder = lang => ({ value: '', text: t(lang, 'agents.pick.choose'), disabled: false });

/**
 * The experiment select: the placeholder, then each experiment as its name
 * and short verdict line. One with no pair, or with no pair that can run, is
 * greyed with the reason of its first pair (runs_sixspeed_18sep: no meta.json).
 */
export function experimentOptions(catalog, lang) {
  return [placeholder(lang), ...(catalog?.experiments || []).map(e => {
    if (!(e.pairs || []).length) {
      return { value: e.runs, text: t(lang, 'agents.pick.experiment_empty', { name: e.name }), disabled: true };
    }
    if (!selectable(e)) {
      return {
        value: e.runs,
        text: t(lang, 'agents.pick.experiment_refused', { name: e.name, reason: e.pairs[0].reason }),
        disabled: true,
      };
    }
    const short = e.verdict?.short?.[lang];
    return { value: e.runs, text: short ? `${e.name} · ${short}` : e.name, disabled: false };
  })];
}

/**
 * The pair select: every pair, its quoted table row; a refused pair greyed
 * with its first problem only, so the option stays one line. refusedPairs
 * carries every problem.
 */
export function pairOptions(experiment, lang) {
  return [placeholder(lang), ...(experiment?.pairs || []).map(p => {
    const value = String(p.seed);
    if (!p.runnable) {
      return { value, text: t(lang, 'agents.pick.pair_refused', { seed: p.seed, reason: p.reason }), disabled: true };
    }
    if (typeof p.table_diff !== 'number') {
      return { value, text: t(lang, 'agents.pick.pair_no_row', { seed: p.seed }), disabled: false };
    }
    return { value, text: t(lang, 'agents.pick.pair_row', { seed: p.seed, diff: formatDiff(p.table_diff) }), disabled: false };
  })];
}

/**
 * Every pair that cannot run, in catalog order, with EVERY problem the server
 * found: both arms, and each stored and live field of a plant mismatch
 * (design section 8, "listed and disabled with reason and fields"). A greyed
 * option has room for the first problem only; the page lists these beside it.
 */
export function refusedPairs(catalog) {
  return (catalog?.experiments || []).flatMap(e => (e.pairs || [])
    .filter(p => !p.runnable)
    .map(p => ({ runs: e.runs, name: e.name, seed: p.seed, problems: [...(p.problems || [])] })));
}

/** The episode select: climb start, grade and the three weights; Phase D says "the same road". */
export function episodeOptions(catalog, pair, lang) {
  const sameRoad = pair?.protocol === 'phase-d';
  return [placeholder(lang), ...episodesOf(catalog, pair).map(e => {
    const weights = { w0: fixed(e.weights?.[0], 2), w1: fixed(e.weights?.[1], 2), w2: fixed(e.weights?.[2], 2) };
    const text = sameRoad
      ? t(lang, 'agents.pick.episode_option_same_road', { idx: e.idx, ...weights })
      : t(lang, 'agents.pick.episode_option', {
        idx: e.idx, start: fixed(e.climb_start_s, 0), grade: percent(e.grade), ...weights,
      });
    return { value: String(e.idx), text, disabled: false };
  })];
}

/**
 * The chosen experiment's WHOLE short verdict line, said under its select. A
 * closed select shows only as much of its option as fits: on 28 Sep at 390 px
 * the C4 option read "C4 · smaller than the MEI (50) at 300 000 steps" and
 * nothing more, the clean negative the short line exists to prevent (design
 * section 6, misreading table). The line is the server's own, found, missing
 * or none alike, exactly as the verdict box prints it; '' when nothing is
 * chosen or the verdict carries no short line.
 */
export function experimentNote(experiment, lang) {
  return experiment?.verdict?.short?.[lang] || '';
}

/**
 * The qualifier under the pair select, by the experiment's protocol: the table
 * row is a difference of medians over twenty episodes, never this episode.
 * Phase D's says "the same road"; '' when the experiment has no protocol.
 */
export function pairQualifier(experiment, lang) {
  if (experiment?.protocol === 'phase-d') return t(lang, 'agents.pick.pair_qualifier_same_road');
  if (experiment?.protocol === 'd2') return t(lang, 'agents.pick.pair_qualifier');
  return '';
}

/** Phase D's one road, said once under the episode select: its climb start and grade. */
export function sameRoadNote(catalog, experiment, lang) {
  if (experiment?.protocol !== 'phase-d') return '';
  const e = catalog?.episodes?.['phase-d']?.[0];
  if (!e) return '';
  return t(lang, 'agents.pick.same_road_note', { start: fixed(e.climb_start_s, 0), grade: percent(e.grade) });
}

// check_pair's three 'scored' values (app/agent_catalog.py), each with its line.
const SCORED = new Map([
  ['match', 'agents.verdict.scored_match'],
  ['not recorded', 'agents.verdict.not_recorded'],
  ['mismatch', 'agents.verdict.scored_mismatch'],
]);

/**
 * The verdict box's line for one agent: is its final.zip the artefact
 * results/ scored? 'mismatch' means results/ records a different zip sha, and
 * the pair is refused. null when the sha check never ran (scored is null: an
 * earlier check refused the pair first), so nothing is claimed either way.
 */
export function scoredKey(scored, resultFile) {
  if (!resultFile) return 'agents.verdict.no_result';
  return SCORED.get(scored) ?? null;
}

/** The blind car's label key: Phase D's blind agent may have memorised its one road. */
export function blindLabelKey(protocol) {
  return protocol === 'phase-d' ? 'agents.car.blind_phase_d' : 'agents.car.blind';
}

/**
 * Where results/ says the blinded arm is not blind, from the verdict's own
 * 'not_blind' quote, so the citation follows the file: results/<file>:<a>-<b>.
 */
export function notBlindCite(verdict) {
  const line = (verdict?.lines || []).find(l => l.key === 'not_blind');
  if (!line) return 'results/PHASE_D_RESULT.txt';
  const n = String(line.text).split('\n').length;
  return `results/${line.file}:${n > 1 ? `${line.line}-${line.line + n - 1}` : line.line}`;
}

// The models panel of /agents: two language models, jev and Laya, asked about
// the paused second (M3 design, docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md
// sections 7.5b, 7.7 and 7.9).
//
// PURE: no page access, no requests, no clock. agents.mjs does the wiring
// (the gesture, the two status requests, the two buttons) and asks this module
// every question that has an answer worth testing, so model-panel.test.mjs
// pins each decision without a browser.
//
// THREE RULES, and they are the design's, not style:
//  - The two columns never meet. Every function takes one model's view, one
//    model's answer or one model's failure; nothing here reads both, so a jev
//    failure (no key, no credit, no network) can never block or blank Laya.
//  - Nothing is computed from an answer. rowView passes the model's own choice,
//    levels and probabilities through, and the order check compares two
//    choices of the same model. No average, no difference, and no comparison
//    with the agents. The model's own confidence is never read (design C9).
//  - Nothing is substituted. An error is its fixed code and that code's
//    sentence; a code this page does not know is a server error with its HTTP
//    status, never the server's text.
import { laneStoppedAt } from './agent-view.mjs';
import { t } from './i18n.mjs';
import './agents-strings.mjs';

const EM_DASH = '—';

export const MODELS = Object.freeze(['jev', 'laya']);

// The five question ids, in engine_env action order, so index i is ACTIONS[i]
// (agent-view.mjs) and row i of app/model_questions.py LEVELS.
export const QUESTION_IDS = Object.freeze(['spark_trim', 'lambda_trim', 'boost_ceiling', 'cooling_fan', 'coolant_pump']);

// Every code the three POST routes answer with (design 7.9, and the jev key
// field of 29 Sep: bad_key and bad_key_request). Each has a sentence
// agents.models.error.<code> in both languages; any other code is shown as
// agents.models.error.server_error with its HTTP status.
export const ERROR_CODES = Object.freeze([
  'no_key', 'network', 'timeout', 'key_rejected', 'vendor_refused', 'request_rejected', 'rate_limited',
  'overloaded', 'vendor_status', 'not_configured', 'not_found', 'start_failed', 'start_timeout',
  'worker_error', 'worker_died', 'network_attempt', 'bad_answer', 'foreign_origin', 'no_trace',
  'step_not_computed', 'busy', 'bad_key', 'bad_key_request',
]);

// Where jev's key came from, as the status route names it. 'page' has a line
// of its own; the other two are words inside the configured line, so no raw
// token shows inside an Arabic line. Any other value reads as a dash.
const JEV_SOURCES = Object.freeze(['env', 'file']);

/**
 * May this model be asked about second k now? view = { playing, waiting, done,
 * frames, inFlight } for ONE model. Design C10: playback stopped (the play
 * button shows play: !playing && !waiting), which includes the natural end of
 * the episode and a finished episode never played; the build finished; frame k
 * exists; the sighted lane had not stopped at or before k; nothing in flight
 * for this model. Returns { enabled, reason }, reason an i18n key or null.
 */
export function askState(view, k) {
  const frames = Array.isArray(view?.frames) ? view.frames : [];
  if (view?.inFlight) return { enabled: false, reason: 'agents.models.reason.asking' };
  if (!view?.done && !frames.length) return { enabled: false, reason: 'agents.pause.empty' };
  if (!view.done) return { enabled: false, reason: 'agents.models.reason.not_done' };
  if (view.playing || view.waiting) return { enabled: false, reason: 'agents.models.reason.pause' };
  if (!Number.isInteger(k) || k < 0 || k >= frames.length) return { enabled: false, reason: 'agents.models.reason.not_done' };
  const stopped = laneStoppedAt(frames, 0);
  if (stopped !== null && stopped <= k) return { enabled: false, reason: 'agents.models.reason.stopped' };
  return { enabled: true, reason: null };
}

/**
 * One model's answers, one per second of the episode on screen, in memory
 * only. put() at a second already held replaces it; clear() empties the map
 * (agents.mjs calls it in compute() and clearEpisode()). An entry is whatever
 * agents.mjs stores: { body } for an answer or { failure } for an error.
 */
export function createAnswers() {
  const map = new Map();
  const id = (key, k) => `${key}#${k}`;
  return {
    put(key, k, entry) { map.set(id(key, k), entry); },
    get(key, k) { return map.has(id(key, k)) ? map.get(id(key, k)) : null; },
    clear() { map.clear(); },
    get size() { return map.size; },
  };
}

/**
 * Row `actionIndex` of one answer body (the POST route's 200 JSON), or null
 * when that action is missing. The five bars follow the options' own order
 * (the design's order), each with its physical level and the model's
 * probability, exactly one marked chosen. `reversed` and `verdict` come from
 * Laya's order check (answers_reversed, design 7.5b): 'held' when the choice
 * is the same with the options reversed, 'changed' when it is not; jev is
 * asked once, so both are null for jev.
 */
export function rowView(answer, actionIndex) {
  const id = QUESTION_IDS[actionIndex];
  const a = id ? answer?.answers?.[id] : undefined;
  if (!a || !Array.isArray(a.options)) return null;
  const r = answer.answers_reversed?.[id] ?? null;
  return {
    id,
    choice: a.choice,
    level: a.level_phys,
    net: a.level_net,
    chosenP: a.chosen_p,
    bars: a.options.map(o => ({ key: o.key, level: o.level_phys, p: a.probabilities?.[o.key], chosen: o.key === a.choice })),
    reversed: r ? { choice: r.choice, level: r.level_phys } : null,
    verdict: r ? (r.choice === a.choice ? 'held' : 'changed') : null,
  };
}

// The kinds a worker_error can carry: app/laya_bridge.py KINDS and the
// 'other' it sends for anything else. The page keeps the same four names, so
// a kind is never text the server was not built to send.
const WORKER_KINDS = Object.freeze(['ValueError', 'RuntimeError', 'OutOfMemoryError', 'other']);

/**
 * What went wrong, from the HTTP status and the JSON body (either may be
 * missing). No status at all is a request that never reached the server:
 * 'server_down'. A body whose code is in ERROR_CODES keeps only that code, an
 * integer status and a kind: one of WORKER_KINDS, 'other' for any other
 * string, null when there is none; anything else (FastAPI's own 500, a 422
 * {detail}, the server's server_error) is 'server_error' with the HTTP status.
 */
export function failureOf(httpStatus, body) {
  if (httpStatus === null || httpStatus === undefined) return { code: 'server_down', status: null, kind: null };
  if (body && typeof body === 'object' && ERROR_CODES.includes(body.code)) {
    const kind = typeof body.kind === 'string' ? body.kind : null;
    return {
      code: body.code,
      status: Number.isInteger(body.status) ? body.status : null,
      kind: kind === null || WORKER_KINDS.includes(kind) ? kind : 'other',
    };
  }
  return { code: 'server_error', status: httpStatus, kind: null };
}

/**
 * The sentence a column shows for a failure: «لا جواب — {code}: {sentence}»
 * for a known code, «لا جواب — {sentence}» for a failed request (the page's
 * own server-down sentence) and for an unknown code (server error, HTTP N).
 */
export function errorText(code, status, lang, kind = null) {
  if (code === 'server_down') {
    return t(lang, 'agents.models.no_answer_plain', { sentence: t(lang, 'agents.load.server_down') });
  }
  if (!ERROR_CODES.includes(code)) {
    return t(lang, 'agents.models.no_answer_plain',
      { sentence: t(lang, 'agents.models.error.server_error', { status: status ?? EM_DASH }) });
  }
  const sentence = t(lang, `agents.models.error.${code}`, { status: status ?? EM_DASH, kind: kind ?? 'other' });
  return t(lang, 'agents.models.no_answer', { code, sentence });
}

/**
 * The sentence jev's key field shows when a save or a clear failed (a
 * failureOf result), in jev's column only: the code's own sentence, the
 * page's server-down sentence for a request that never reached the server,
 * and a server error with its HTTP status for anything else. Nothing the
 * server sent is shown but its code.
 */
export function keyErrorText(failure, lang) {
  if (failure.code === 'server_down') return t(lang, 'agents.load.server_down');
  if (!ERROR_CODES.includes(failure.code)) {
    return t(lang, 'agents.models.error.server_error', { status: failure.status ?? EM_DASH });
  }
  return t(lang, `agents.models.error.${failure.code}`, { status: failure.status ?? EM_DASH, kind: failure.kind ?? 'other' });
}

/**
 * One model's status line, from its GET status route. A failed status request
 * (failure) shows its error here, in this column only. jev says whether a key
 * is configured and where from (the page, the environment variable or a
 * file), never the key; Laya says what its worker is doing, and reads
 * 'starting' while its first press is in flight.
 */
export function statusLine(name, status, failure, inFlight, lang) {
  if (failure) return errorText(failure.code, failure.status, lang, failure.kind);
  if (!status) return EM_DASH;
  if (name === 'jev') {
    if (!status.configured) return t(lang, 'agents.models.jev.status.no_key');
    if (status.source === 'page') return t(lang, 'agents.models.jev.status.page');
    const source = JEV_SOURCES.includes(status.source) ? t(lang, `agents.models.jev.source.${status.source}`) : EM_DASH;
    return t(lang, 'agents.models.jev.status.configured', { source });
  }
  if (status.problem === 'not_configured') return t(lang, 'agents.models.laya.status.not_configured');
  if (status.problem === 'not_found') return t(lang, 'agents.models.laya.status.not_found');
  if (status.worker === 'ready') return t(lang, 'agents.models.laya.status.ready', { device: status.device ?? EM_DASH });
  if (status.worker === 'starting' || inFlight) return t(lang, 'agents.models.laya.status.starting');
  if (status.worker === 'failed') return t(lang, 'agents.models.laya.status.failed', { code: status.problem ?? EM_DASH });
  return t(lang, 'agents.models.laya.status.stopped');
}

// Pure presentation logic, no DOM and no physics. Everything here is a
// function of one replay frame plus a language, so it can be tested without a
// browser. main.mjs owns the DOM; this file owns what the DOM is allowed to
// say, and i18n.mjs owns the words it says it in.
import { t, DEFAULT_LANG } from './i18n.mjs';

export const EM_DASH = '—';

export const num = v => (typeof v === 'number' && Number.isFinite(v) ? v : null);
export const fmt = (v, digits = 0) => (num(v) === null ? EM_DASH : v.toFixed(digits));

/** What the gear strip and its source label must say for this frame. */
export function gearState(frame, lang = DEFAULT_LANG) {
  const gear = frame ? num(frame.gear) : null;
  const source = (frame && frame.gear_source) || 'unavailable';
  // A gear with no source, or a source with no gear, would let the strip light
  // a cell the inference did not actually resolve.
  const resolved = gear !== null && source !== 'unavailable' ? gear : null;
  const noteKey = frame && frame.gear_note ? `gear.note.${frame.gear_note}` : null;
  const base = (noteKey && t(lang, noteKey)) || t(lang, 'gear.note.waiting');
  const err = frame ? num(frame.ratio_error) : null;
  return {
    gear: resolved,
    source,
    estimated: source === 'estimated',
    sourceText: t(lang, `source.${source}`) || t(lang, 'source.unavailable'),
    note: err === null ? base
      : t(lang, 'gear.note_with_ratio_error', { note: base, pct: (err * 100).toFixed(1) }),
  };
}

/**
 * H / tau for the live card. tau is the Estimator's own flow-dependent turbine
 * time constant, carried on the frame; this never recomputes or assumes it.
 * Returns dashes rather than a number whenever tau is missing or non-physical.
 */
export function horizonRatio(horizonS, tauS) {
  const tau = num(tauS);
  const h = num(horizonS);
  if (tau === null || tau <= 0 || h === null || h <= 0) {
    return { tauText: EM_DASH, ratio: null, ratioText: EM_DASH };
  }
  const ratio = h / tau;
  return { tauText: `${tau.toFixed(0)} s`, ratio, ratioText: ratio.toFixed(2) };
}

/** The preview caption must never imply a predictive controller is running. */
export function previewCaption(preview, lang = DEFAULT_LANG) {
  if (!preview || preview.distance_m === null || preview.distance_m === undefined) {
    return t(lang, 'preview.caption.no_distance');
  }
  if (preview.complete) return t(lang, 'preview.caption.complete');
  return t(lang, 'preview.caption.partial', { seconds: preview.covered_s.toFixed(0) });
}

// ------------------------------------------------------------------ charts
export const CHART_W = 620;
export const CHART_H = 150;
export const PAD_X = 4;
export const PAD_Y = 10;
const CHART_POINTS = 1100;

/** Keep the endpoints; a chart that drops the last sample misreports the end. */
export function thin(frames, limit = CHART_POINTS) {
  const stride = Math.max(1, Math.ceil(frames.length / limit));
  if (stride === 1) return frames.slice();
  const out = [];
  for (let i = 0; i < frames.length; i += stride) out.push(frames[i]);
  const last = frames[frames.length - 1];
  if (out.length && out[out.length - 1] !== last) out.push(last);
  return out;
}

/**
 * One SVG path for one channel. A logger gap or a missing value lifts the pen:
 * a straight line across a hole is an invented measurement.
 */
export function channelPath(points, key, duration) {
  const values = points.map(f => num(f[key])).filter(v => v !== null);
  if (values.length < 2) return null;
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (hi - lo < 1e-9) { lo -= 0.5; hi += 0.5; }
  let d = '';
  let pen = false;
  for (const f of points) {
    const v = num(f[key]);
    if (v === null || f.gap) { pen = false; continue; }
    const x = PAD_X + (duration > 0 ? f.t / duration : 0) * (CHART_W - 2 * PAD_X);
    const y = CHART_H - PAD_Y - ((v - lo) / (hi - lo)) * (CHART_H - 2 * PAD_Y);
    d += `${pen ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)} `;
    pen = true;
  }
  return d.trim() ? { d: d.trim(), lo, hi } : null;
}

/** Y for the cursor dot, or null when this sample has nothing to point at. */
export function cursorY(path, value, gap) {
  const v = num(value);
  if (!path || v === null || gap) return null;
  return CHART_H - PAD_Y - ((v - path.lo) / (path.hi - path.lo)) * (CHART_H - 2 * PAD_Y);
}

export function cursorX(time, duration) {
  const t = duration > 0 ? Math.min(1, Math.max(0, time / duration)) : 0;
  return PAD_X + t * (CHART_W - 2 * PAD_X);
}

// ------------------------------------------------- turbine threshold
/**
 * How close the ESTIMATED turbine housing is to the protection threshold.
 *
 * TWO signals, because one is not enough.
 *
 * NEAR_K = 50 is the VALUE band. Measured against the shipped drives, only one
 * of the ten crosses the limit and the next hottest -- the two-hour
 * Jeddah-Taif mountain run -- peaks about 52 K short, so it falls just OUTSIDE
 * this band. That is stated rather than tuned away: widening the band until a
 * drive lights up would be choosing a threshold to produce an indication.
 *
 * The band alone therefore cannot warn early, and that is why the second
 * signal exists. The housing is a first-order node, so it can read far below
 * the limit while climbing steadily towards a steady state above it. When the
 * steady state implied by the CURRENT operating point is at or above the
 * limit, the state is "approaching" whatever the present value is. That number
 * is the Estimator's own fixed point, not a new model and not a trend
 * extrapolation -- AUDIT.md M10 records that projecting the trend linearly is
 * wrong on this node.
 *
 * Two things this must never imply: the threshold is a limit THIS PROJECT
 * chose, not a manufacturer rating, and the temperature it is compared against
 * is a model output whose heat capacity is assumed. Callers show both.
 */
export const NEAR_K = 50;

export function thresholdState(turbineC, limitC, steadyC) {
  const v = num(turbineC);
  const limit = num(limitC);
  if (v === null || limit === null) {
    return { level: 'none', margin: null, over: null, heading: false };
  }
  // Heading there: holding this operating point would take the housing over
  // the limit, whatever it reads right now. This is the early warning; the
  // value band alone cannot give one on a first-order node.
  const steady = num(steadyC);
  const heading = steady !== null && steady >= limit;
  if (v >= limit) return { level: 'over', margin: 0, over: v - limit, heading };
  const margin = limit - v;
  return { level: margin <= NEAR_K || heading ? 'near' : 'normal', margin, over: null, heading };
}

/**
 * Contiguous spans where the estimate sat at or above the threshold, plus the
 * total time. A logger gap ends a span rather than being counted through it:
 * nothing was measured there, so nothing can be claimed about it.
 */
export function thresholdSpans(frames, limitC) {
  const limit = num(limitC);
  const spans = [];
  let total = 0;
  if (limit === null) return { spans, total_s: 0 };
  let open = null;
  for (let i = 0; i < frames.length; i++) {
    const f = frames[i];
    const v = num(f.turbine_c);
    const above = v !== null && v >= limit && !f.gap;
    if (above && open === null) open = f.t;
    if (!above && open !== null) {
      spans.push({ from: open, to: frames[i - 1].t });
      total += frames[i - 1].t - open;
      open = null;
    }
  }
  if (open !== null) {
    const last = frames[frames.length - 1].t;
    spans.push({ from: open, to: last });
    total += last - open;
  }
  return { spans, total_s: total };
}

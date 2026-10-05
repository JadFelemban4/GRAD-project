// Number formatting and bidi isolates for the results tab (/results).
//
// PURE: no DOM, no fetch, no physics. Every number the tab writes goes through
// here, so the spec's typographic rules (section 7.2) hold everywhere:
//  - a negative number takes U+2212 MINUS SIGN, never an ASCII hyphen;
//  - thousands are grouped with U+202F NARROW NO-BREAK SPACE, whose bidi class
//    (CS) keeps a grouped number whole inside an Arabic line, where U+2009
//    (WS) would split it;
//  - inside Arabic text a number, hash, date or path is a left-to-right
//    isolate, U+2066 ... U+2069: isolateLtr from agent-picker.mjs, exported
//    here as ltr so the tab has one source for it.
// The three constants are written as escapes, never as the characters: the
// Write tool on this machine decodes a typed escape, so this file is written
// by a Python script and byte-checked (results-format.test.mjs pins both).
//
// ROUNDING is toFixed's, applied to the magnitude, so a negative rounds as its
// positive does. A value stored exactly at a half rounds away from zero
// (1.25 -> 1.3, -1.25 -> -1.3), as agent-picker.mjs formatDiff rounds, so the
// two pages print the same digits for the same number; a value stored just
// under a half rounds down (1.005 -> 1.00). Python's format() rounds an exact
// half to even (1.25 -> 1.2); the tab prints a file's numbers at the digits
// the file printed them with, where no such tie can arise.
import { isolateLtr } from './agent-picker.mjs';

export const EM_DASH = '\u2014';
export const MINUS = '\u2212';
export const NNBSP = '\u202f';

/** `text` inside a left-to-right isolate, U+2066 ... U+2069 (agent-picker.mjs). */
export const ltr = isolateLtr;

const finite = v => typeof v === 'number' && Number.isFinite(v);

/**
 * `v` with `digits` decimals. A negative takes U+2212; a value that rounds to
 * zero carries no sign ("0.0", never "-0.0"); a missing or non-finite value is
 * an em dash. Not grouped: a file's numbers keep the shape the file printed.
 */
export function fmtNum(v, digits) {
  if (!finite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(digits);
  return v < 0 && Number(text) !== 0 ? `${MINUS}${text}` : text;
}

/**
 * As fmtNum, and always signed: '+' for a positive value or one that rounds
 * to zero ("+0.0"), U+2212 for a negative one.
 */
export function fmtSigned(v, digits) {
  if (!finite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(digits);
  return `${v < 0 && Number(text) !== 0 ? MINUS : '+'}${text}`;
}

/**
 * A whole number: Math.round of the magnitude (so -2.5 gives -3, as 2.5 gives
 * 3), grouped in thousands with U+202F from 1000 up, U+2212 for a negative.
 */
export function fmtInt(v) {
  if (!finite(v)) return EM_DASH;
  const n = Math.round(Math.abs(v));
  const text = String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NNBSP);
  return v < 0 && n !== 0 ? `${MINUS}${text}` : text;
}

/** `text` isolated left to right inside an Arabic line; in English, as it is. */
export function inline(lang, text) {
  return lang === 'ar' ? ltr(text) : text;
}

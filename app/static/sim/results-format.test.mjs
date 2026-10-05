// results-format.mjs: how the results tab writes a number, and the left-to-right
// isolates it puts around one inside an Arabic line (spec section 7.2).
//
// Characters that are invisible or look like ASCII (U+2066 and U+2069, the
// isolates; U+2212 MINUS SIGN; U+202F NARROW NO-BREAK SPACE) are built here from
// their code points, and an escape's TEXT from String.fromCharCode(92): the
// Write tool on this machine decodes a typed backslash-u escape into the
// character. The last test checks that this file keeps to that rule.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { isolateLtr, formatDiff } from './agent-picker.mjs';
import { EM_DASH, MINUS, NNBSP, ltr, fmtNum, fmtSigned, fmtInt, inline } from './results-format.mjs?v=R1a';

const cp = n => String.fromCodePoint(n);
const LRI = cp(0x2066);
const PDI = cp(0x2069);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;
// Invisible, or easily taken for ASCII: never literal in a source file.
const INVISIBLE = [0x061c, 0x200b, 0x200e, 0x200f, 0x2011, 0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x202f, 0x2066, 0x2067, 0x2068, 0x2069, 0x2212, 0xfeff];
const NOT_A_NUMBER = [null, undefined, NaN, Infinity, -Infinity, '12', true, {}];

test('the constants are the characters the spec names, and ltr is the isolate /agents uses', () => {
  assert.equal(EM_DASH, cp(0x2014));
  assert.equal(MINUS, cp(0x2212));
  assert.equal(NNBSP, cp(0x202f));
  assert.equal(ltr, isolateLtr);
  assert.equal(ltr('7'), `${LRI}7${PDI}`);
});

// The decision this file pins: toFixed on the MAGNITUDE. An exact binary half
// rounds away from zero, in both signs, as formatDiff on /agents does. Python's
// format() would give 1.2 for 1.25 (half to even); the tab never re-rounds a
// file's printed digits, so the two never meet on a tie.
test('fmtNum rounds the magnitude as toFixed does, writes U+2212 and never a negative zero', () => {
  assert.equal(fmtNum(920.1, 1), '920.1');
  assert.equal(fmtNum(-12.34, 1), `${MINUS}12.3`);
  assert.equal(fmtNum(-1.25, 1), `${MINUS}1.3`);
  assert.equal(fmtNum(1.25, 1), '1.3');
  assert.equal(fmtNum(0.125, 2), '0.13');
  assert.equal(fmtNum(1.005, 2), '1.00', '1.005 is stored just under the half, and toFixed reads the stored value');
  assert.equal(fmtNum(-0.04, 1), '0.0');
  assert.equal(fmtNum(-0, 1), '0.0');
  assert.equal(fmtNum(0, 0), '0');
  assert.equal(fmtNum(2527, 1), '2527.0', 'fmtNum does not group: a file\'s number keeps its printed shape');
  assert.ok(!fmtNum(-3, 1).includes('-'), 'an ASCII hyphen is not a minus sign');
});

test('fmtSigned always carries a sign, and agrees with formatDiff on /agents digit for digit', () => {
  assert.equal(fmtSigned(0, 1), '+0.0');
  assert.equal(fmtSigned(-2, 1), `${MINUS}2.0`);
  assert.equal(fmtSigned(2, 1), '+2.0');
  assert.equal(fmtSigned(-0.04, 1), '+0.0');
  assert.equal(fmtSigned(360.6, 1), '+360.6');
  assert.equal(fmtSigned(-1.25, 1), `${MINUS}1.3`);
  assert.equal(fmtSigned(-0.5, 0), `${MINUS}1`);
  for (const v of [-360.6, -9.8, -1.25, -0.04, 0, 0.04, 0.05, 1.25, 30.2]) {
    assert.equal(ltr(fmtSigned(v, 1)), formatDiff(v), `fmtSigned(${v}) differs from formatDiff`);
  }
});

test('fmtInt rounds, groups thousands with U+202F from 1000 up, and writes U+2212', () => {
  assert.equal(fmtInt(300000), `300${NNBSP}000`);
  assert.equal(fmtInt(50000), `50${NNBSP}000`);
  assert.equal(fmtInt(950), '950');
  assert.equal(fmtInt(999), '999');
  assert.equal(fmtInt(1000), `1${NNBSP}000`);
  assert.equal(fmtInt(1234567), `1${NNBSP}234${NNBSP}567`);
  assert.equal(fmtInt(-1234), `${MINUS}1${NNBSP}234`);
  assert.equal(fmtInt(999.5), `1${NNBSP}000`);
  assert.equal(fmtInt(2.5), '3');
  assert.equal(fmtInt(-2.5), `${MINUS}3`, 'the magnitude is rounded, so -2.5 mirrors 2.5');
  assert.equal(fmtInt(-0.4), '0');
  assert.equal(fmtInt(20), '20');
});

test('inline isolates in Arabic only', () => {
  assert.equal(inline('ar', 'x'), `${LRI}x${PDI}`);
  assert.equal(inline('en', 'x'), 'x');
  assert.equal(inline('ar', fmtInt(300000)), `${LRI}300${NNBSP}000${PDI}`);
  assert.equal(inline('en', fmtSigned(-2, 1)), `${MINUS}2.0`);
});

test('a missing or non-finite value is an em dash in every formatter', () => {
  for (const bad of NOT_A_NUMBER) {
    assert.equal(fmtNum(bad, 1), EM_DASH, `fmtNum(${String(bad)})`);
    assert.equal(fmtSigned(bad, 1), EM_DASH, `fmtSigned(${String(bad)})`);
    assert.equal(fmtInt(bad), EM_DASH, `fmtInt(${String(bad)})`);
  }
});

test('results-format.mjs carries its three characters as escapes, never literally', () => {
  const src = readFileSync(new URL('./results-format.mjs', import.meta.url), 'utf8');
  for (const code of INVISIBLE) {
    assert.equal(src.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in results-format.mjs: write the escape`);
  }
  for (const hex of ['2014', '2212', '202f']) {
    assert.equal(src.split(escapeText(hex)).length - 1, 1, `the escape of U+${hex} must appear exactly once`);
  }
  assert.match(src, /^import \{ isolateLtr \} from '\.\/agent-picker\.mjs';$/m, 'the isolate comes from agent-picker.mjs, unversioned');
});

test('this file builds its characters from code points, never from a typed escape', () => {
  const own = readFileSync(new URL(import.meta.url), 'utf8');
  for (const code of INVISIBLE) assert.equal(own.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in this test file`);
  assert.equal(own.split(escapeText('')).length - 1, 0, 'a typed backslash-u escape in this test file');
});

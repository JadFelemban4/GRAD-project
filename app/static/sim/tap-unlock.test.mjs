// The hidden gesture of /agents (M3 design 7.7): ten taps within 4000 ms on
// the footer label '02 — AGENTS' show the models panel. The counter is pure
// and lives in a closure, so a reload forgets the unlock; the source must use
// no browser storage at all.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createTapUnlock } from './tap-unlock.mjs';

// n taps spread evenly from 0 to spanMs; returns what each tap() answered.
function taps(gesture, n, spanMs, start = 0) {
  return Array.from({ length: n }, (_, i) => gesture.tap(start + (n > 1 ? i * spanMs / (n - 1) : 0)));
}

test('ten taps spread over 4000 ms unlock, on the tenth only', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 10, 4000), [...Array(9).fill(false), true]);
});

test('nine taps do not unlock', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 9, 900), Array(9).fill(false));
});

test('ten taps over 4001 ms do not unlock: the first has left the window', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 10, 4001), Array(10).fill(false));
});

test('the defaults are ten taps in 4000 ms', () => {
  assert.equal(taps(createTapUnlock(), 10, 4000).at(-1), true);
  assert.equal(taps(createTapUnlock(), 10, 4001).at(-1), false);
  assert.equal(taps(createTapUnlock(), 9, 100).at(-1), false);
});

test('after an unlock the count starts again from zero', () => {
  const gesture = createTapUnlock({ taps: 10, windowMs: 4000 });
  assert.equal(taps(gesture, 10, 900).at(-1), true);
  // The tenth tap reset the count: one more tap is one tap, not eleven.
  assert.equal(gesture.tap(1000), false);
  assert.deepEqual(taps(gesture, 9, 900, 1100), [...Array(8).fill(false), true]);
});

test('the gesture keeps nothing outside its closure', () => {
  const src = readFileSync(new URL('./tap-unlock.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(src, /localStorage|sessionStorage|indexedDB|cookie/);
  // No page access and no clock of its own: agents.mjs passes each tap's time.
  assert.doesNotMatch(src, /\bfetch\s*\(|\bdocument\.|\bwindow\.|\bglobalThis\b|\bDate\.now\b|\bperformance\.now\b/);
});

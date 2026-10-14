import test from 'node:test';
import assert from 'node:assert/strict';
import { createChartSelection } from './chart-selection.mjs?v=R1a';

test('cursor accepts only its dataset generation and axis', () => {
  const store = createChartSelection({ sourceRevision: 'set:a', axisKind: 'time' });
  assert.equal(store.set({ sourceRevision: 'set:b', axisKind: 'time', sampleIndex: 2 }), false);
  assert.equal(store.set({ sourceRevision: 'set:a', axisKind: 'episode', sampleIndex: 2 }), false);
  assert.equal(store.set({ sourceRevision: 'set:a', axisKind: 'time', sampleIndex: 2 }), true);
  assert.equal(store.get().sampleIndex, 2);
  assert.equal(store.set({ sourceRevision: 'set:a', axisKind: 'time', sampleIndex: -1 }), false);
  assert.equal(store.get().sampleIndex, 2);
});
test('pair selection notifies once, can reset, and unsubscribes', () => {
  const store = createChartSelection({ sourceRevision: 'a', axisKind: 'pair' });
  const received = [];
  const stop = store.subscribe(s => received.push(s));
  const next = { sourceRevision: 'a', axisKind: 'pair', pairSeed: 0 };
  store.set(next); store.set(next);
  assert.equal(received.length, 1);
  assert.ok(Object.isFrozen(store.get()));
  store.reset(); assert.equal(received.length, 2);
  stop(); store.set(next); assert.equal(received.length, 2);
});

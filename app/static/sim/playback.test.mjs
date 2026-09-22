import test from 'node:test';
import assert from 'node:assert/strict';
let module;
try { module = await import('./playback.mjs'); } catch { /* asserted below */ }
const api = () => { assert.ok(module, 'playback module must be implemented'); return module; };
const frames = [
  { t: 0, s_m: 0, speed_kmh: 36, rpm: 2400, gear: 2, turbine_c: 300, gap: false },
  { t: 1, s_m: 10, speed_kmh: 36, rpm: 1500, gear: 3, turbine_c: 310, gap: false },
  { t: 3, s_m: 30, speed_kmh: 36, rpm: 1600, gear: 3, turbine_c: 330, gap: false },
];
test('pause holds time; rate advances only presentation and restart resets', () => {
  const { PlaybackClock } = api(); const c = new PlaybackClock(30);
  c.play(0); assert.equal(c.tick(1000), 1); c.pause(1000);
  assert.equal(c.tick(21000), 1); c.setRate(4, 21000); c.play(21000);
  assert.equal(c.tick(23000), 9); c.reset(24000);
  assert.equal(c.time, 0); assert.equal(c.playing, false);
});
test('seek selects one exact sample for rpm, gear and temperature without blended shifts', () => {
  const { sampleAt } = api();
  assert.equal(sampleAt(frames, .99).frame, frames[0]);
  assert.equal(sampleAt(frames, 1).frame, frames[1]);
  assert.equal(sampleAt(frames, .5).distance_m, 5);
  assert.equal(sampleAt(frames, 0).frame.gear, 2);
});
test('different playback rates land on the identical sample at the same trip time', () => {
  const { PlaybackClock, sampleAt } = api();
  const slow = new PlaybackClock(3), fast = new PlaybackClock(3);
  slow.play(0); fast.setRate(8, 0); fast.play(0);
  assert.equal(sampleAt(frames, slow.tick(2000)).frame, sampleAt(frames, fast.tick(250)).frame);
});
test('preview integrates speed and clips to available trip end', () => {
  const { previewAt } = api();
  const p = previewAt(frames, .5, 30);
  assert.equal(p.distance_m, 25); assert.equal(p.covered_s, 2.5); assert.equal(p.complete, false);
});
test('logger gaps and missing speed block invented distance', () => {
  const { sampleAt, previewAt } = api();
  const broken = [frames[0], { ...frames[1], t: 20, s_m: 0, gap: true }];
  assert.equal(sampleAt(broken, 10).distance_m, null);
  assert.equal(previewAt(broken, 0, 10).distance_m, null);
  assert.equal(sampleAt([{ ...frames[0], s_m: null, speed_kmh: null }], 0).distance_m, null);
});
test('clock clamps at end and rejects invalid rates; seeks preserve pause state', () => {
  const { PlaybackClock } = api(); const c = new PlaybackClock(3);
  c.seek(1, 0); assert.equal(c.playing, false);
  c.play(0); assert.equal(c.tick(5000), 3); assert.equal(c.playing, false);
  assert.throws(() => c.setRate(0, 5000));
});

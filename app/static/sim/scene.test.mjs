import test from 'node:test';
import assert from 'node:assert/strict';
import { createRoad, previewWorldLength, METERS_PER_WORLD_UNIT } from './geometry.mjs';

test('distance mapping crosses the loop seam without a position or heading jump', () => {
  const road = createRoad();
  const before = road.atDistance(road.length - 0.0001);
  const after = road.atDistance(road.length + 0.0001);
  assert.ok(Math.hypot(...before.position.map((v, i) => v - after.position[i])) < 0.0003);
  assert.ok(before.tangent.reduce((sum, v, i) => sum + v * after.tangent[i], 0) > 0.9999);
});

test('equal travelled distances give approximately equal spatial steps on bends and slopes', () => {
  const road = createRoad();
  assert.ok(road.length > 100);
  for (let d = 0; d < road.length; d += 0.73) {
    const a = road.atDistance(d).position;
    const b = road.atDistance(d + 0.1).position;
    const step = Math.hypot(...a.map((v, i) => v - b[i]));
    assert.ok(Math.abs(step - 0.1) < 0.0008, `step at ${d} was ${step}`);
  }
});

test('the loop contains a flat start, a climb, and a descent', () => {
  const road = createRoad();
  assert.ok(Math.abs(road.atDistance(0).tangent[1]) < 0.001);
  const slopes = Array.from({ length: 100 }, (_, i) => road.atDistance(i / 100 * road.length).tangent[1]);
  assert.ok(Math.max(...slopes) > 0.06);
  assert.ok(Math.min(...slopes) < -0.06);
});

test('preview uses the replay distance scale and clips oversized horizons to one lap', () => {
  const road = createRoad();
  assert.ok(Math.abs(previewWorldLength(1000, road.length) * METERS_PER_WORLD_UNIT - 1000) < 1e-9);
  assert.ok(previewWorldLength(1000, road.length) < road.length / 4);
  assert.equal(previewWorldLength(1e9, road.length), road.length);
  for (const value of [null, undefined, NaN, Infinity, -50]) assert.equal(previewWorldLength(value, road.length), 0);
});

test('the viewing scale keeps a slow cruise and a hard pull visibly different', () => {
  // At the old 90 m/unit a 60 km/h cruise took 292 s to cross the view and
  // 164 km/h took 107 s: the ratio was right and both read as stationary, so
  // the two were indistinguishable on screen. This pins the fix.
  const road = createRoad();
  const VIEW_UNITS = 54;              // orthographic extent 27, so 54 across
  const cross = kmh => VIEW_UNITS / ((kmh / 3.6) / METERS_PER_WORLD_UNIT);

  // A hard pull must cross the visible scene in well under a minute.
  assert.ok(cross(164) < 60, `164 km/h takes ${cross(164).toFixed(0)} s to cross the view`);
  // The ratio is physics and must survive any scale change.
  assert.ok(Math.abs(cross(60) / cross(164) - 164 / 60) < 1e-9);
  // And the scale must stay above the floor the preview assertion needs.
  assert.ok(previewWorldLength(1000, road.length) < road.length / 4);
});

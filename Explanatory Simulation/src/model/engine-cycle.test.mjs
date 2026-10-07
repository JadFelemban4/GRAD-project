import test from 'node:test';
import assert from 'node:assert/strict';
const cycle = await import('./engine-cycle.mjs').catch(() => ({}));
const { cylinderPose } = await import('./layout.mjs');

test('four named strokes follow the modeled valve windows across a 720 degree teaching cycle', () => {
  const { STROKE_STATIONS, strokeAtDegrees } = cycle;
  assert.equal(typeof strokeAtDegrees, 'function', 'named stroke stations must be available');
  assert.deepEqual([0, 90, 180, 270, 360, 450, 540, 630, 720].map(angle => strokeAtDegrees(angle).name),
    ['سحب', 'سحب', 'ضغط', 'ضغط', 'قدرة', 'قدرة', 'عادم', 'عادم', 'سحب']);
  assert.deepEqual(STROKE_STATIONS.map(station => station.angle), [90, 270, 450, 630]);
  assert.equal(strokeAtDegrees(90).intakeOpen, true);
  assert.equal(strokeAtDegrees(90).exhaustOpen, false);
  assert.equal(strokeAtDegrees(630).exhaustOpen, true);
});

test('scrubbing the chosen cylinder keeps its own labelled angle when other cylinders are offset', () => {
  const { cylinderCycleDegrees, globalCycleForCylinder } = cycle;
  assert.equal(typeof globalCycleForCylinder, 'function', 'chosen-cylinder phase must be available');
  for (const index of [0, 2, 5]) {
    assert.ok(Math.abs(cylinderCycleDegrees(globalCycleForCylinder(450, index), index) - 450) < 1e-9);
  }
});

test('piston direction and both valve states agree with the mechanical phase at every station', () => {
  for (const station of cycle.STROKE_STATIONS) {
    const before = cylinderPose((station.angle - 1) / 720).pistonY;
    const after = cylinderPose((station.angle + 1) / 720).pistonY;
    assert.equal(station.pistonDirection, after > before ? 'up' : 'down');
    assert.equal(station.intakeOpen, station.id === 'intake');
    assert.equal(station.exhaustOpen, station.id === 'exhaust');
  }
});

import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { TURBO_CENTER, turboAnchors, turboFlowPaths, turboFlowData, flowVisual, turboHousingPosition } from './turbo-layout.mjs';

test('turbo data conserves the supplied air-plus-fuel exhaust mass flow without mutating the frame', () => {
  const frame = Object.freeze({ mdot_air: 18.5, mdot_fuel: 0.9, t_turb: 930 });
  const before = { ...frame };
  assert.deepEqual(turboFlowData(frame), { air: 18.5, exhaust: 19.4 });
  assert.deepEqual(frame, before);
});

test('invalid or incomplete mass-flow values remain unavailable', () => {
  assert.deepEqual(turboFlowData(null), { air: null, exhaust: null });
  assert.deepEqual(turboFlowData({ mdot_air: -1, mdot_fuel: 0.2 }), { air: null, exhaust: null });
  assert.deepEqual(turboFlowData({ mdot_air: 2, mdot_fuel: Number.NaN }), { air: 2, exhaust: null });
  assert.deepEqual(turboFlowData({ mdot_air: Infinity, mdot_fuel: 0 }), { air: null, exhaust: null });
});

test('illustrative packet mapping increases monotonically and caps without changing input', () => {
  const frame = Object.freeze({ mdot_air: 7, mdot_fuel: 0.4 });
  const rates = [0, 5, 20, 45, 250, 500];
  const mapping = rates.map(flowVisual);
  for (let i = 1; i < mapping.length; i++) {
    assert.ok(mapping[i].speed >= mapping[i - 1].speed);
    assert.ok(mapping[i].density >= mapping[i - 1].density);
  }
  assert.ok(mapping[3].speed < mapping[4].speed, 'ordinary rates remain visually distinct');
  assert.deepEqual(mapping[4], mapping[5], 'display mapping is capped');
  assert.equal(flowVisual(-0.1), null);
  assert.equal(flowVisual(Number.NaN), null);
  turboFlowData(frame);
  assert.deepEqual(frame, { mdot_air: 7, mdot_fuel: 0.4 });
});

test('shaft anchors join both rotors and all sampled flow guides fit the stated envelope', () => {
  const compressor = new THREE.Vector3(...turboAnchors.compressor);
  const turbine = new THREE.Vector3(...turboAnchors.turbine);
  assert.equal(TURBO_CENTER[1], 0.85);
  assert.ok(compressor.z > 0 && turbine.z < 0);
  assert.ok(compressor.distanceTo(turbine) < 1.1, 'one continuous shaft reaches both rotor hubs');
  for (const [name, points] of Object.entries(turboFlowPaths)) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
    for (let i = 0; i <= 240; i++) {
      const point = curve.getPoint(i / 240);
      const radius = 0.013;
      assert.ok(point.x - radius >= -1.2 && point.x + radius <= 1.2, `${name} x outside bounds`);
      assert.ok(point.y - radius >= 0.15 && point.y + radius <= 1.8, `${name} y outside bounds`);
      assert.ok(point.z - radius >= -1.0 && point.z + radius <= 1.0, `${name} z outside bounds`);
    }
  }
});

test('housing separation is symmetric and returns exactly to the original center', () => {
  assert.deepEqual(turboHousingPosition('compressor', 0), [...turboAnchors.compressor]);
  assert.deepEqual(turboHousingPosition('turbine', 0), [...turboAnchors.turbine]);
  assert.ok(turboHousingPosition('compressor', 1)[2] > turboHousingPosition('compressor', 0)[2]);
  assert.ok(turboHousingPosition('turbine', 1)[2] < turboHousingPosition('turbine', 0)[2]);
  assert.deepEqual(turboHousingPosition('compressor', 0), [...turboAnchors.compressor]);
});

test('paused rotor phase stays fixed across flow changes and resumes from the retained angle', async () => {
  const { advanceTurboPhase } = await import('./turbo-layout.mjs');
  assert.equal(advanceTurboPhase(0.4, 0, 7), 0.4);
  assert.equal(advanceTurboPhase(0.4, 0, 2), 0.4);
  assert.equal(advanceTurboPhase(0.4, 0.05, 2), 0.5);
  assert.equal(advanceTurboPhase(0.5, 0.05, 7), 0.8500000000000001);
  assert.ok(advanceTurboPhase(6.2, 0.1, 2) < 0.2);
});

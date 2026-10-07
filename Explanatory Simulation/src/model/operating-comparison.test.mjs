import test from 'node:test';
import assert from 'node:assert/strict';
import { captureOperatingBaseline, compareOperatingResults } from './operating-comparison.mjs';

const makeInputs = () => ({ rpm: 2500, map_kpa: 100, spark: 15, lam: 1 });
const makePlant = () => ({ torque_nm: 220, egt_c: 780, mdot_fuel_gps: 12, mdot_air_gps: 150 });

test('baseline snapshots inputs and measured plant outputs without retaining mutable aliases', () => {
  const inputs = makeInputs();
  const plant = makePlant();
  const baseline = captureOperatingBaseline({ inputs, result: plant });
  inputs.rpm = 6000;
  plant.torque_nm = 0;

  assert.equal(baseline.inputs.rpm, 2500);
  assert.equal(baseline.result.torque_nm, 220);
  assert.equal(Object.isFrozen(baseline), true);
  assert.equal(Object.isFrozen(baseline.inputs), true);
  assert.equal(Object.isFrozen(baseline.result), true);
});

test('missing or non-finite readings remain unavailable and do not produce deltas', () => {
  assert.equal(captureOperatingBaseline(null), null);
  const baseline = captureOperatingBaseline({ inputs: makeInputs(), result: { ...makePlant(), egt_c: Infinity } });
  const rows = compareOperatingResults({ torque_nm: null, egt_c: 900, mdot_fuel_gps: NaN, mdot_air_gps: 155 }, baseline);

  assert.equal(baseline.result.egt_c, null);
  assert.deepEqual(rows.find(row => row.key === 'torque_nm'), { key: 'torque_nm', baseline: 220, current: null, delta: null, unit: 'Nm' });
  assert.deepEqual(rows.find(row => row.key === 'egt_c'), { key: 'egt_c', baseline: null, current: 900, delta: null, unit: '°C' });
  assert.equal(rows.find(row => row.key === 'mdot_fuel_gps').current, null);
  assert.equal(rows.find(row => row.key === 'mdot_fuel_gps').delta, null);
});

test('zero is a valid reading and deltas retain positive and negative signs', () => {
  const baseline = captureOperatingBaseline({ inputs: makeInputs(), result: { torque_nm: 0, egt_c: 800, mdot_fuel_gps: 10, mdot_air_gps: 140 } });
  const rows = compareOperatingResults({ torque_nm: 0, egt_c: 780, mdot_fuel_gps: 11.5, mdot_air_gps: 135 }, baseline);

  assert.equal(rows.find(row => row.key === 'torque_nm').delta, 0);
  assert.equal(rows.find(row => row.key === 'egt_c').delta, -20);
  assert.equal(rows.find(row => row.key === 'mdot_fuel_gps').delta, 1.5);
  assert.equal(rows.find(row => row.key === 'mdot_air_gps').delta, -5);
});

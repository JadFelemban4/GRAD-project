import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {
  VEHICLE_TURBO_MOUNT, vehicleTurboAnchors, vehicleAirflowPaths,
  mountedTurboPoint,
} from './vehicle-airflow.mjs';
import { turboFlowPaths } from './turbo-layout.mjs';

test('scaled turbo ports align exactly with the external vehicle pipes', () => {
  assert.deepEqual(vehicleTurboAnchors.compressorInlet, mountedTurboPoint(turboFlowPaths.airInlet[0]));
  assert.deepEqual(vehicleTurboAnchors.compressorOutlet, mountedTurboPoint(turboFlowPaths.airCharge.at(-1)));
  assert.deepEqual(vehicleTurboAnchors.turbineInlet, mountedTurboPoint(turboFlowPaths.exhaustInlet[0]));
  assert.deepEqual(vehicleTurboAnchors.turbineOutlet, mountedTurboPoint(turboFlowPaths.exhaustOutlet.at(-1)));
  const localCenter = mountedTurboPoint([0, 0.85, 0]);
  assert.ok(localCenter.every((v, i) => Math.abs(v - [2.06, 0.94, 0.62][i]) < 1e-12));
  assert.equal(VEHICLE_TURBO_MOUNT.scale, 0.22);
});

test('internal solid airflow and exhaust pipes remain within the source coupe bounds', () => {
  const names = ['filterToCompressor', 'compressorToCooler', 'coolerToIntake', 'exhaustManifoldToTurbine', 'turbineToTailpipe'];
  for (const name of names) {
    const points = vehicleAirflowPaths[name];
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
    for (let i = 0; i <= 200; i++) {
      const p = curve.getPoint(i / 200);
      const radius = name.startsWith('exhaust') || name === 'turbineToTailpipe' ? 0.035 : 0.033;
      assert.ok(p.x - radius >= -3.2 && p.x + radius <= 3.32, `${name} leaves coupe in X`);
      assert.ok(p.y - radius >= 0 && p.y + radius <= 2.2, `${name} leaves coupe in Y`);
      assert.ok(p.z - radius >= -1.486 && p.z + radius <= 1.486, `${name} leaves coupe in Z`);
    }
  }
  for (const [i, points] of vehicleAirflowPaths.exhaustRunners.entries()) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
    for (let j = 0; j <= 200; j++) {
      const p = curve.getPoint(j / 200);
      assert.ok(p.x - 0.022 >= -3.2 && p.x + 0.022 <= 3.32, `runner ${i} leaves coupe in X`);
      assert.ok(p.y - 0.022 >= 0 && p.y + 0.022 <= 2.2, `runner ${i} leaves coupe in Y`);
      assert.ok(p.z - 0.022 >= -1.486 && p.z + 0.022 <= 1.486, `runner ${i} leaves coupe in Z`);
    }
  }
});

test('outside air enters at the front and tailpipe exhaust exits at the rear', () => {
  const air = vehicleAirflowPaths.airOutside;
  const exhaust = vehicleAirflowPaths.exhaustOutside;
  assert.ok(air[0][0] > 3.32, 'air begins beyond the front bumper');
  assert.ok(air.at(-1)[0] < 3.32, 'air reaches the filter inside the coupe');
  assert.ok(exhaust[0][0] >= -3.2, 'exhaust path begins at the tailpipe');
  assert.ok(exhaust.at(-1)[0] < -3.2, 'exhaust packets leave behind the rear bumper');
});

test('every cylinder has a continuous intake and exhaust route across the head boundary', async () => {
  const { cylinderX, headPortAnchors } = await import('./engine-ports.mjs').catch(() => ({}));
  assert.equal(typeof headPortAnchors, 'function', 'head port anchors must be shared by both assemblies');
  assert.equal(vehicleAirflowPaths.intakeBranches.length, 6);
  assert.equal(vehicleAirflowPaths.exhaustRunners.length, 6);
  for (let index = 0; index < 6; index++) {
    const ports = headPortAnchors(index);
    assert.equal(ports.intake.valve[0], cylinderX(index));
    assert.deepEqual(vehicleAirflowPaths.intakeBranches[index].at(-1), ports.intake.head);
    assert.deepEqual(vehicleAirflowPaths.exhaustRunners[index][0], ports.exhaust.head);
    assert.deepEqual(ports.intake.passage[0], ports.intake.head);
    assert.deepEqual(ports.intake.passage.at(-1), ports.intake.valve);
    assert.deepEqual(ports.exhaust.passage[0], ports.exhaust.valve);
    assert.deepEqual(ports.exhaust.passage.at(-1), ports.exhaust.head);
    assert.ok(ports.intake.head[2] < ports.intake.valve[2], 'intake port opens from the intake side');
    assert.ok(ports.exhaust.head[2] > ports.exhaust.valve[2], 'exhaust port opens toward the exhaust manifold');
  }
  assert.deepEqual(vehicleAirflowPaths.coolerToIntake.at(-1), vehicleAirflowPaths.intakePlenumLeft[0]);
  assert.deepEqual(vehicleAirflowPaths.coolerToIntake.at(-1), vehicleAirflowPaths.intakePlenumRight[0]);
});

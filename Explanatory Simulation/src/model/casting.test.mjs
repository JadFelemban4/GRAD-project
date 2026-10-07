import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { beveledBox } from './casting.mjs';

test('beveled castings preserve requested engine datums and dimensions', () => {
  for (const size of [[1.48, 0.36, 0.58], [1.38, 0.17, 0.55], [1.48, 0.04, 0.58]]) {
    const geometry = beveledBox(size, false);
    const bounds = geometry.boundingBox ?? (geometry.computeBoundingBox(), geometry.boundingBox);
    const actual = bounds.getSize(new THREE.Vector3());
    assert.ok(actual.distanceTo(new THREE.Vector3(...size)) < 1e-6, `expected ${size}, got ${actual.toArray()}`);
    assert.ok(bounds.min.distanceTo(new THREE.Vector3(...size.map((v) => -v / 2))) < 1e-6);
    geometry.dispose();
  }
});

test('section casting removes the top and near-side faces but retains exact envelope', () => {
  const geometry = beveledBox([1.48, 0.36, 0.58], true);
  const bounds = geometry.boundingBox ?? (geometry.computeBoundingBox(), geometry.boundingBox);
  const size = bounds.getSize(new THREE.Vector3());
  assert.ok(size.distanceTo(new THREE.Vector3(1.48, 0.36, 0.58)) < 1e-6);

  const positions = geometry.getAttribute('position');
  const normals = geometry.getAttribute('normal');
  const index = geometry.index;
  const count = index?.count ?? positions.count;
  let faces = 0;
  for (let i = 0; i < count; i += 3) {
    const a = index?.getX(i) ?? i;
    const b = index?.getX(i + 1) ?? i + 1;
    const c = index?.getX(i + 2) ?? i + 2;
    const ny = (normals.getY(a) + normals.getY(b) + normals.getY(c)) / 3;
    const nz = (normals.getZ(a) + normals.getZ(b) + normals.getZ(c)) / 3;
    assert.ok(ny < 0.9, 'top cap is removed');
    assert.ok(nz < 0.9, 'near-side cap is removed');
    faces++;
  }
  assert.ok(faces > 0, 'section still has structural wall faces');
  geometry.dispose();
});

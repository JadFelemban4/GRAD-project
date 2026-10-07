import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { createSupraModel } from './supra.mjs';

test('procedural Supra has expected coupe proportions and independently controllable shell', () => {
  const { root, wheels, shellMaterials } = createSupraModel();
  const bounds = new THREE.Box3().setFromObject(root);
  const size = bounds.getSize(new THREE.Vector3());
  assert.equal(wheels.length, 4);
  assert.ok(size.x > 6.2 && size.x < 7.2, `unexpected length ${size.x}`);
  assert.ok(size.y > 1.9 && size.y < 2.6, `unexpected height ${size.y}`);
  assert.ok(size.z > 2.6 && size.z < 3.2, `unexpected width ${size.z}`);

  const meshes = [];
  root.traverse((node) => { if (node.isMesh) meshes.push(node); });
  const shellMeshes = meshes.filter((mesh) => mesh.userData.component === 'body-shell');
  const glassMeshes = meshes.filter((mesh) => mesh.userData.component === 'glazing');
  assert.ok(shellMeshes.length >= 2, 'body panels are identified as shell parts');
  assert.ok(glassMeshes.length >= 1, 'greenhouse glass is identified separately');
  assert.ok(shellMaterials.length >= 1);
  assert.ok(shellMeshes.every((mesh) => shellMaterials.includes(mesh.material)));
  assert.ok(glassMeshes.every((mesh) => mesh.material !== shellMaterials[0]));
  assert.ok(meshes.filter((mesh) => mesh.material.transparent).every((mesh) => mesh.material.opacity < 0.7));

  root.traverse((node) => {
    if (node.isMesh) {
      node.geometry.dispose();
      if (Array.isArray(node.material)) node.material.forEach((material) => material.dispose());
      else node.material.dispose();
    }
  });
});

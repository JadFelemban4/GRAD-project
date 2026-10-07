import * as THREE from 'three';

/** Build a chamfered cast form centred at the origin with an exact outer size. */
export function beveledBox(size, section = false, bevel = 0.02) {
  const [sx, sy, sz] = size;
  const b = Math.min(bevel, sx * 0.12, sy * 0.22, sz * 0.12);
  const shape = new THREE.Shape();
  shape.moveTo(-sx / 2 + b, -sy / 2 + b);
  shape.lineTo(sx / 2 - b, -sy / 2 + b);
  shape.lineTo(sx / 2 - b, sy / 2 - b);
  shape.lineTo(-sx / 2 + b, sy / 2 - b);
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: sz - 2 * b,
    bevelEnabled: true,
    bevelThickness: b,
    bevelSize: b,
    bevelSegments: 2,
    curveSegments: 2,
    steps: 1,
  });
  geometry.computeBoundingBox();
  const initialBounds = geometry.boundingBox;
  const initialSize = initialBounds.getSize(new THREE.Vector3());
  geometry.scale(sx / initialSize.x, sy / initialSize.y, sz / initialSize.z);
  geometry.computeBoundingBox();
  const center = geometry.boundingBox.getCenter(new THREE.Vector3());
  geometry.translate(-center.x, -center.y, -center.z);

  if (section) {
    if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
    const normal = geometry.getAttribute('normal');
    const sourceIndex = geometry.index;
    const count = sourceIndex?.count ?? geometry.getAttribute('position').count;
    const kept = [];
    for (let i = 0; i < count; i += 3) {
      const a = sourceIndex?.getX(i) ?? i;
      const b1 = sourceIndex?.getX(i + 1) ?? i + 1;
      const c = sourceIndex?.getX(i + 2) ?? i + 2;
      const nz = (normal.getZ(a) + normal.getZ(b1) + normal.getZ(c)) / 3;
      const ny = (normal.getY(a) + normal.getY(b1) + normal.getY(c)) / 3;
      if (nz > 0.9 || ny > 0.9) continue;
      kept.push(a, b1, c);
    }
    geometry.setIndex(kept);
    geometry.clearGroups();
  }

  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

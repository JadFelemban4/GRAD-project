import type * as THREE from 'three';

export function beveledBox(
  size: [number, number, number],
  section?: boolean,
  bevel?: number,
): THREE.BufferGeometry;

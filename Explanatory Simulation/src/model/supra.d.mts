import type * as THREE from 'three';

export interface SupraModel {
  root: THREE.Group;
  wheels: THREE.Group[];
  shellMaterials: THREE.Material[];
}

export function createSupraModel(): SupraModel;

import * as THREE from 'three';
import { supra } from './source-scene.mjs';

const COLORS = {
  carBody: 0xf6f1dc,
  carGlass: 0x334b47,
  carTrim: 0x252d2d,
  carAlloy: 0xb8bcae,
  carAccent: 0x5e706b,
  headlight: 0xe7e7d7,
  taillight: 0x852d2c,
};

/**
 * Create the project's procedural Supra coupe. Geometry is reused from the
 * shipped simulator; materials are kept separate so the viewer can reveal
 * the cabin or tint the body without rebuilding the car.
 */
export function createSupraModel() {
  const materials = new Map();
  const paint = {
    mat(key, options = {}) {
      if (materials.has(key)) return materials.get(key);
      const color = COLORS[key] ?? 0x737a7b;
      let material;
      if (key === 'carGlass') {
        material = new THREE.MeshPhysicalMaterial({ color, roughness: 0.2, metalness: 0.12, side: THREE.DoubleSide, transparent: true, opacity: 0.58, depthWrite: false, ...options });
      } else {
        material = new THREE.MeshStandardMaterial({ color, roughness: 0.42, metalness: 0.16, ...options });
      }
      materials.set(key, material);
      return material;
    },
    loose(key, options = {}) {
      return new THREE.MeshStandardMaterial({ color: 0x737a7b, roughness: 0.42, ...options });
    },
    glow() {
      // The source builder creates headlamp spill meshes for night scenes.
      // Keep their geometry for fidelity, but suppress the daytime glow.
      return new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
    },
  };

  const holder = new THREE.Group();
  holder.name = 'Procedural Supra';
  const { car, wheels } = supra(holder, paint);
  car.name = 'Supra coupe body';

  const shellMaterial = materials.get('carBody');
  const glassMaterial = materials.get('carGlass');
  const shellMaterials = shellMaterial ? [shellMaterial] : [];
  const daylightSuppressed = [];
  car.traverse((object) => {
    if (!object.isMesh) return;
    if (object.material.isMeshBasicMaterial && object.material.opacity === 0) {
      // The simulator's night-light beams extend well beyond the body. Their
      // daytime opacity is zero, so omit them from this daylight model too.
      object.visible = false;
      daylightSuppressed.push(object);
      return;
    }
    object.userData.component = object.material === shellMaterial ? 'body-shell'
      : object.material === glassMaterial ? 'glazing'
        : 'trim';
    object.castShadow = true;
    object.receiveShadow = true;
  });
  daylightSuppressed.forEach((mesh) => {
    mesh.parent?.remove(mesh);
    mesh.geometry.dispose();
    mesh.material.dispose();
  });
  wheels.forEach((wheel, index) => {
    wheel.name = `wheel-${index + 1}`;
    wheel.userData.component = 'wheel';
  });
  // The source's long hood accents were horizontal boxes: their front ends
  // floated above the sloping bonnet. Fit those two decorative creases to
  // the original hood surface, without changing the coupe's source loft.
  const hoodAccents = car.children.filter((object) => object.isMesh && object.material === materials.get('carAccent') && object.position.x === 1.55);
  hoodAccents.forEach((object) => {
    const side = Math.sign(object.position.z);
    car.remove(object);
    object.geometry.dispose();
    const hoodTop = x => x <= 2.25 ? 1.26 + (x - .8) / 1.45 * (1.18 - 1.26) : 1.18 + (x - 2.25) * (.94 - 1.18);
    const hoodWidth = x => x <= 2.25 ? 1.2 + (x - .8) / 1.45 * .09 : 1.29 + (x - 2.25) * (.98 - 1.29);
    const points = [.8, 1.3, 1.8, 2.25, 2.55].map(x => new THREE.Vector3(x, hoodTop(x) + .08 * (1 - .56 / (hoodWidth(x) * .86)) + .01, side * .56));
    const line = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 20, .012, 6, false), materials.get('carAccent'));
    line.userData.component = 'trim';
    car.add(line);
  });
  holder.remove(car);

  return { root: car, wheels, shellMaterials };
}


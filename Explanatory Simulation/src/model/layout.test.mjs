import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {routes,cylinderPose} from './layout.mjs';
import {createSupraModel} from './supra.mjs';

test('every sampled pipe surface stays inside the original vehicle envelope',()=>{
  const {root}=createSupraModel();const bounds=new THREE.Box3().setFromObject(root);
  for(const [name,points] of Object.entries(routes)) {
    const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)),false,'centripetal');
    for(let i=0;i<=200;i++) {
      const p=curve.getPoint(i/200),r=.034;
      assert.ok(p.x-r>=bounds.min.x&&p.x+r<=bounds.max.x,`${name} protrudes along X`);
      assert.ok(p.y-r>=bounds.min.y&&p.y+r<=bounds.max.y,`${name} protrudes along Y`);
      assert.ok(p.z-r>=bounds.min.z&&p.z+r<=bounds.max.z,`${name} protrudes along Z`);
      // All under-bonnet routes fit below the lowest local bonnet crown.
      if(p.x>.8&&name!=='tail') {
        const top=p.x<=2.25?1.26+(p.x-.8)/1.45*(1.18-1.26):1.18+(p.x-2.25)*(.94-1.18);
        const width=p.x<=2.25?1.2+(p.x-.8)/1.45*.09:1.29+(p.x-2.25)*(.98-1.29);
        const surface=top+.08*(1-Math.abs(p.z)/(width*.86));
        assert.ok(p.y+r<=surface,`${name} rises through the bonnet at ${p.toArray()}`);
      }
    }
  }
});
test('six-cylinder teaching motion keeps connecting rods attached and pistons inside sleeves',()=>{
  for(let i=0;i<=720;i++) {
    const p=cylinderPose(i/720);
    assert.ok(Math.abs(Math.hypot(p.jointY-p.pinY,p.pinZ)-.27)<1e-10);
    assert.ok(p.pistonY+.065/2<=1.07,'piston exits the sleeve top');
    assert.ok(p.pistonY-.065/2>=.71,'piston exits the sleeve bottom');
  }
  assert.ok(cylinderPose(0).pistonY>cylinderPose(.25).pistonY);
  assert.equal(cylinderPose(0).pistonY,cylinderPose(.5).pistonY);
});

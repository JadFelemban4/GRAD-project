// Geometry adapted from Explanatory Simulation's EngineAssembly / TurboAssembly.
// A static inline-six cutaway: no combustion, RPM or motion is inferred from time.
// The caller owns temperature materials and the existing recorded-frame contract.
import * as THREE from 'three';
import { beveledBox } from './engine-casting.mjs';

export function createEngineAssembly({block,oil,metal,dark}) {
  const root=new THREE.Group();root.name='inline-six-engine-assembly';
  root.scale.setScalar(4.5);root.position.set(-1.49*4.5,-.56*4.5,.06*4.5);
  const brass=new THREE.MeshStandardMaterial({color:0xb88b55,metalness:.78,roughness:.3});
  const ceramic=new THREE.MeshStandardMaterial({color:0xd5dedc,metalness:.18,roughness:.27});
  const liner=metal.clone();liner.side=THREE.DoubleSide;
  const casting=block;casting.side=THREE.DoubleSide;
  function part(parent,geometry,material,position,name){
    const item=new THREE.Mesh(geometry,material);item.position.set(...position);
    if(name)item.name=name;parent.add(item);return item;
  }
  const box=(size,material,position,name,section=false,bevel=.02)=>
    part(root,beveledBox(size,section,bevel),material,position,name);
  box([1.48,.36,.58],casting,[1.49,.72,-.06],'engine-block',true,.026);
  box([1.48,.04,.58],metal,[1.49,1.06,-.06],'engine-head',true,.007);
  box([1.38,.17,.55],oil,[1.49,.5,-.06],'engine-oil-pan',false,.022);
  box([1.04,.035,.39],dark,[1.49,.397,-.06],'engine-sump',false,.008);
  for(let i=0;i<5;i++)box([.035,.22,.018],metal,[1.02+i*.235,.72,-.355]);
  for(let i=0;i<10;i++){
    const bolt=part(root,new THREE.CylinderGeometry(.013,.013,.012,10),metal,
      [.86+(i%5)*.305,.875,i<5?.235:-.355]);bolt.rotation.x=Math.PI/2;
  }
  const crank=part(root,new THREE.CylinderGeometry(.035,.035,1.34,28),metal,
    [1.49,.59,-.06],'engine-crankshaft');crank.rotation.z=Math.PI/2;
  for(let i=0;i<6;i++){
    const x=.97+i*.21;
    const bore=part(root,new THREE.CylinderGeometry(.078,.078,.36,32,1,true,Math.PI/2,Math.PI),liner,
      [x,.89,-.06],`engine-bore-${i+1}`);bore.userData.part='bore';
    const piston=new THREE.Group();piston.name=`engine-piston-${i+1}`;piston.userData.part='piston';
    piston.position.set(x,.985,-.06);root.add(piston);
    part(piston,new THREE.CylinderGeometry(.073,.076,.065,32),metal,[0,0,0]);
    for(const offset of [-.017,0,.017]){
      const ring=part(piston,new THREE.TorusGeometry(.071,.0032,6,28),offset===0?dark:brass,[0,offset,0]);
      ring.rotation.x=Math.PI/2;
    }
    part(root,new THREE.CylinderGeometry(.017,.027,.36,12),brass,[x,.772,-.06],`engine-rod-${i+1}`);
    const journal=part(root,new THREE.TorusGeometry(.046,.008,8,20),dark,[x,.59,-.06]);journal.rotation.y=Math.PI/2;
    for(const z of [-.094,-.026]){
      part(root,new THREE.CylinderGeometry(.018,.018,.006,20),brass,[x,1.047,z]);
      part(root,new THREE.CylinderGeometry(.004,.004,.065,10),metal,[x,1.081,z]);
    }
    part(root,new THREE.CylinderGeometry(.012,.014,.036,12),metal,[x,1.098,-.06]);
    part(root,new THREE.CylinderGeometry(.009,.009,.026,12),ceramic,[x,1.129,-.06]);
    part(root,new THREE.CylinderGeometry(.013,.013,.006,6),brass,[x,1.142,-.06]);
  }
  for(const z of [-.094,-.026]){
    const cam=part(root,new THREE.CylinderGeometry(.011,.011,1.25,24),metal,[1.49,1.14,z]);cam.rotation.z=Math.PI/2;
    for(let i=0;i<6;i++){
      const lobe=part(root,new THREE.TorusGeometry(.014,.004,8,16),brass,[.97+i*.21,1.14,z]);
      lobe.rotation.y=Math.PI/2;lobe.scale.y=1.45;
    }
  }
  const gear=part(root,new THREE.CylinderGeometry(.074,.074,.045,32),brass,[2.12,1.14,-.06]);gear.rotation.z=Math.PI/2;
  for(let i=0;i<12;i++){
    const a=i*Math.PI/6;box([.042,.019,.018],metal,[2.12,1.14+Math.cos(a)*.074,-.06+Math.sin(a)*.074]);
  }
  const rail=part(root,new THREE.CylinderGeometry(.012,.012,1.26,12),brass,[1.49,1.184,-.245]);rail.rotation.z=Math.PI/2;
  for(let i=0;i<6;i++)part(root,new THREE.CylinderGeometry(.012,.012,.066,12),brass,[.97+i*.21,1.13,-.245]);
  return root;
}

export function turboScrollGeometry(compressor) {
  const points=[],start=compressor?-.35:Math.PI-.35;
  for(let i=0;i<=72;i++){
    const t=i/72,a=start+Math.PI*1.9*t,r=.45+.24*t;
    points.push(new THREE.Vector3(Math.cos(a)*r,Math.sin(a)*r,0));
  }
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points,false,'centripetal'),96,.16,12,false);
}

export function turboBladeGeometry() {
  const shape=new THREE.Shape();shape.moveTo(.055,-.022);
  shape.quadraticCurveTo(.14,-.065,.30,.045);shape.quadraticCurveTo(.34,.075,.315,.105);
  shape.quadraticCurveTo(.18,.025,.065,.025);shape.quadraticCurveTo(.042,.005,.055,-.022);
  const geometry=new THREE.ExtrudeGeometry(shape,{depth:.06,bevelEnabled:false,curveSegments:5});
  geometry.translate(0,0,-.03);geometry.scale(1.5,1.5,1);return geometry;
}

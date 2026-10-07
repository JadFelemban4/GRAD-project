import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import * as ports from './engine-ports.mjs';
import { cylinderPose } from './layout.mjs';
import { strokeAtDegrees } from './engine-cycle.mjs';
const G = ports.GAS_GEOMETRY;
const routeCurve = ports.gasFlowCurve;
test('gas route connects manifolds and chamber and full glyphs clear both valves, piston and sleeve',()=>{
 for(let index=0;index<6;index++)for(const side of ['intake','exhaust']){
  const p=ports.headPortAnchors(index), path=p[side], curve=routeCurve(path.flow), checks=[];
  assert.deepEqual(path.flow[0],side==='intake'?path.head:path.chamber);
  assert.deepEqual(path.flow.at(-1),side==='intake'?path.chamber:path.head);
  for(let k=0;k<=1600;k++)checks.push({v:curve.getPoint(k/1600),r:G.packetRadius});
  for(const t of G.arrowStations){
   const cone=new THREE.ConeGeometry(G.arrowRadius,G.arrowHeight,10), q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),curve.getTangent(t).normalize());
   for(let k=0;k<cone.attributes.position.count;k++)checks.push({v:new THREE.Vector3().fromBufferAttribute(cone.attributes.position,k).applyQuaternion(q).add(curve.getPoint(t)),r:0});
   cone.dispose();
  }
  let crossed=0;
  for(const {v,r} of checks){
   if(Math.abs(v.y-(path.valve[1]-.015))<.004)crossed++;
   // Include packets whose lower hemisphere reaches the sleeve's top plane.
   if(v.y-r<=ports.CYLINDER_BORE.y+ports.CYLINDER_BORE.height/2){
    assert.ok(Math.abs(Math.hypot(v.x-ports.cylinderX(index),v.z-ports.CYLINDER_BORE.z)-ports.CYLINDER_BORE.radius)>r+1e-7,`${side}: sleeve glyph`);
   }
   const start=side==='intake'?0:540;
   for(const a of [...Array.from({length:180},(_,n)=>start+n),start+179.999999]){
    const phase=strokeAtDegrees(a);
    for(const other of ['intake','exhaust']){
     const valve=p[other].valve,V=ports.VALVE_GEOMETRY,y=valve[1]-(phase[other+'Open']?V.lift:0),rad=Math.hypot(v.x-valve[0],v.z-valve[2]);
     const distance=(radius,center,half)=>Math.hypot(Math.max(0,rad-radius),Math.max(0,Math.abs(v.y-center)-half));
     assert.ok(distance(V.stemRadius,y+V.stemOffset,V.stemHeight/2)>r+1e-7,`${side}: full glyph intersects ${other} stem`);
     assert.ok(distance(V.discRadius,y,V.discHeight/2)>r+1e-7,`${side}: full glyph intersects ${other} disc`);
    }
    assert.ok(Math.hypot(Math.max(0,Math.hypot(v.x-ports.cylinderX(index),v.z-ports.CYLINDER_BORE.z)-.076),Math.max(0,Math.abs(v.y-cylinderPose(a/720).pistonY)-.065/2))>r+1e-7,`${side}: piston glyph`);
   }
  }
  assert.ok(crossed>0,'cross the lifted disc height beside its edge');
  assert.deepEqual(p.intake.chamber,ports.fuelRouteAnchors(index).flow.at(-1));
 }
});
test('gas availability follows actual valve phases and suppresses detached and muted flow',()=>{
 assert.equal(typeof ports.gasFlowAvailable,'function');
 for(let a=0;a<720;a++)for(const side of ['intake','exhaust']){
  assert.equal(ports.gasFlowAvailable(a,side),strokeAtDegrees(a)[side+'Open']);
  assert.equal(ports.gasFlowAvailable(a,side,false),false);
  assert.equal(ports.gasFlowAvailable(a,side,true,true),false);
 }
 for(const a of [NaN,Infinity])assert.equal(ports.gasFlowAvailable(a,'intake'),false);
 for(const amount of [.01,.25,1])assert.equal(ports.headPortAnchors(0,amount).flowConnected,false);
});
test('charge never uses the solid stem centre as a packet station',()=>{
 const p=ports.headPortAnchors(0),curve=routeCurve(p.intake.flow);
 const valve=p.intake.valve,V=ports.VALVE_GEOMETRY,y=valve[1]-V.lift+V.stemOffset;
 for(let k=0;k<=1600;k++){
  const v=curve.getPoint(k/1600),rad=Math.hypot(v.x-valve[0],v.z-valve[2]);
  assert.ok(Math.hypot(Math.max(0,rad-V.stemRadius),Math.max(0,Math.abs(v.y-y)-V.stemHeight/2))>G.packetRadius,'packet intersects intake solid stem');
 }
});



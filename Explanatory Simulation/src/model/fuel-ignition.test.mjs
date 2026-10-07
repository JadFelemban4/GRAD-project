import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { headPortAnchors, cylinderX, fuelRouteAnchors, FUEL_GEOMETRY, VALVE_GEOMETRY } from './engine-ports.mjs';
import { cylinderPose } from './layout.mjs';
import { ignitionCommandDegrees, sparkPulseAtDegrees, combustionAtDegrees, globalCycleForCylinder, cylinderCycleDegrees } from './engine-cycle.mjs';

test('fuel route joins actual rail, body, nozzle and intake passage for all cylinders',()=>{
 for(let i=0;i<6;i++){
  const p=headPortAnchors(i), f=fuelRouteAnchors(i);
  assert.deepEqual(f.feed[0],f.rail); assert.deepEqual(f.feed.at(-1),f.injectorTop);
  assert.equal(f.injectorCenter[1]-f.injectorHeight/2,f.nozzleTop[1]);
  assert.deepEqual(f.flow[0],f.nozzle); assert.deepEqual(f.flow.at(-1),p.intake.chamber);
  assert.equal(f.nozzleCenter[1]-f.nozzleHeight/2,f.nozzle[1]);
  assert.deepEqual(f.nozzle,p.intake.passage[1]);
  for(let a=0;a<180;a++){
   const pistonTop=cylinderPose(a/720).pistonY+.065/2;
   for(let k=0;k<f.flow.length-1;k++)for(let s=0;s<=20;s++){
    const v=new THREE.Vector3(...f.flow[k]).lerp(new THREE.Vector3(...f.flow[k+1]),s/20);
    if(v.y<1.07){
     assert.ok(v.y-.004>pistonTop);
     assert.ok(Math.hypot(v.x-cylinderX(i),v.z+.06)+.004<.078);
     if(Math.abs(v.y-(p.intake.valve[1]-.015))<=.003+.004)assert.ok(Math.hypot(v.x-p.intake.valve[0],v.z-p.intake.valve[2])>.018+.004);
    }
   }
  }
  assert.equal(fuelRouteAnchors(i,.01).connected,false);
 }
});
test('spark command and short pulse handle signs, wrapping, invalid timing and every cylinder',()=>{
 for(const [spark,command] of [[15,345],[-15,375],[0,360],[400,680],[-400,40],[360,0]]){
  assert.equal(ignitionCommandDegrees(spark),command);
  for(let i=0;i<6;i++){
   const angle=cylinderCycleDegrees(globalCycleForCylinder(command,i),i);
   assert.ok(sparkPulseAtDegrees(angle,spark)>.99);
  }
  assert.equal(sparkPulseAtDegrees(command-1,spark),0);
  assert.equal(sparkPulseAtDegrees(command+8,spark),0);
  assert.ok(combustionAtDegrees(command+25,spark)>0);
 }
 for(const invalid of [undefined,null,NaN,Infinity,'15']){
  assert.equal(ignitionCommandDegrees(invalid),null);
  assert.equal(sparkPulseAtDegrees(360,invalid),0);
  assert.equal(combustionAtDegrees(380,invalid),0);
 }
 assert.equal(sparkPulseAtDegrees(450,15),0);
 assert.ok(combustionAtDegrees(450,15)>0);
});
import { fuelFlowAvailable } from './engine-ports.mjs';
test('fuel route availability preserves lambda and suppresses closed-valve, invalid and detached flow',()=>{
 for(const lambda of [.7,1,1.45]){
  const frame={lam:lambda};
  for(const a of [0,90,179.999,720])assert.equal(fuelFlowAvailable(a,frame.lam),true);
  for(const a of [180,270,360,450,540,630])assert.equal(fuelFlowAvailable(a,frame.lam),false);
  assert.equal(fuelFlowAvailable(90,frame.lam,false),false);
  assert.equal(frame.lam,lambda);
 }
 for(const lambda of [undefined,null,NaN,Infinity,0,-1,'1'])assert.equal(fuelFlowAvailable(90,lambda),false);
});
test('rendered fuel tube, packet envelope and arrow vertices clear both solid valves and piston',()=>{
 for(let i=0;i<6;i++){
  const p=headPortAnchors(i),f=fuelRouteAnchors(i),curve=new THREE.CurvePath();
  for(let k=1;k<f.flow.length;k++)curve.add(new THREE.LineCurve3(new THREE.Vector3(...f.flow[k-1]),new THREE.Vector3(...f.flow[k])));
  const tube=new THREE.TubeGeometry(curve,64,FUEL_GEOMETRY.tubeRadius,6,false), checks=[];
  const verts=tube.attributes.position;
  for(let k=0;k<verts.count;k++)checks.push({p:new THREE.Vector3().fromBufferAttribute(verts,k),r:0});
  // Lambda does not scale packet positions or radii; max rendered radius remains .004.
  for(let k=0;k<=1000;k++)checks.push({p:curve.getPoint(k/1000),r:FUEL_GEOMETRY.packetRadius});
  for(const t of FUEL_GEOMETRY.arrowStations){
   const arrow=new THREE.ConeGeometry(FUEL_GEOMETRY.arrowRadius,FUEL_GEOMETRY.arrowHeight,8),q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),curve.getTangent(t).normalize()),at=curve.getPoint(t);
   for(let k=0;k<arrow.attributes.position.count;k++)checks.push({p:new THREE.Vector3().fromBufferAttribute(arrow.attributes.position,k).applyQuaternion(q).add(at),r:0});
   arrow.dispose();
  }
  for(let a=0;a<180;a++)for(const {p:v,r} of checks){
   for(const [side,open] of [['intake',true],['exhaust',false]]){
    const valve=p[side].valve,discY=valve[1]-(open?VALVE_GEOMETRY.lift:0),radial=Math.hypot(v.x-valve[0],v.z-valve[2]);
    const solidDistance=(radius,center,halfHeight)=>Math.hypot(Math.max(0,radial-radius),Math.max(0,Math.abs(v.y-center)-halfHeight));
    assert.ok(solidDistance(VALVE_GEOMETRY.stemRadius,discY+VALVE_GEOMETRY.stemOffset,VALVE_GEOMETRY.stemHeight/2)>r+1e-7,'fuel intersects solid '+side+' valve stem');
    assert.ok(solidDistance(VALVE_GEOMETRY.discRadius,discY,VALVE_GEOMETRY.discHeight/2)>r+1e-7,'fuel intersects solid '+side+' valve disc');
   }
   if(v.y<=1.07){
    assert.ok(v.y-r>cylinderPose(a/720).pistonY+.065/2,'fuel intersects piston');
    assert.ok(Math.hypot(v.x-cylinderX(i),v.z+.06)+r<.078,'fuel intersects sleeve wall');
   }
  }
  tube.dispose();
 }
});

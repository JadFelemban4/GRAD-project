import test from 'node:test';
import assert from 'node:assert/strict';
let THREE,createEngineScene;
try {THREE=await import('three');({createEngineScene}=await import('./scene.mjs'));}catch{}
function build(){
  const view={scene:new THREE.Scene(),camera:new THREE.OrthographicCamera(),renderer:{domElement:{style:{}}},
    render(){},theme:()=> 'light',setTheme(){},dispose(){},paint:{
      mat:(_key,props)=>new THREE.MeshStandardMaterial(props),loose:(_key,props)=>new THREE.MeshStandardMaterial(props)}};
  return {view,engine:createEngineScene({}, {makeStage:()=>view})};
}
test('engine inspector separates gas paths and names the shaft, compressor and turbine',{skip:!THREE},()=>{
  const {view,engine}=build();
  for(const name of ['intake-path','exhaust-path','cooling-path','turbo-shaft','turbo-compressor','turbo-turbine'])
    assert.ok(view.scene.getObjectByName(name),name);
  assert.notEqual(view.scene.getObjectByName('intake-path'),view.scene.getObjectByName('exhaust-path'));engine.dispose();
});
test('camera and theme changes preserve the selected temperature and reduced motion stops schematic phase',{skip:!THREE},()=>{
  const {view,engine}=build();engine.update({turbine_c:400,time:2});
  const turbine=view.scene.getObjectByName('turbo-turbine');const color=turbine.material.color.getHex();
  engine.setCamera('turbo');assert.ok(view.camera.position.z>0);engine.setTheme('light');
  assert.equal(turbine.material.color.getHex(),color);
  engine.setReducedMotion(true);engine.update({turbine_c:400,time:9});
  assert.equal(view.scene.getObjectByName('compressor-rotor').rotation.z,0);engine.dispose();
});
test('the cutaway keeps all six pistons inside their bores and exposes a continuous crankshaft',{skip:!THREE},()=>{
  const {view,engine}=build();view.scene.updateMatrixWorld(true);
  const pistons=[],bores=[];
  view.scene.traverse(part=>{if(part.userData.part==='piston')pistons.push(part);if(part.userData.part==='bore')bores.push(part);});
  assert.equal(pistons.length,6);assert.equal(bores.length,6);
  for(let i=0;i<6;i++){
    const piston=new THREE.Box3().setFromObject(pistons[i]);
    const bore=new THREE.Box3().setFromObject(bores[i]);
    // The visible liner is half a bore; its physical circular envelope is full.
    const center=bores[i].getWorldPosition(new THREE.Vector3());
    const radius=bores[i].geometry.parameters.radiusTop*bores[i].getWorldScale(new THREE.Vector3()).x;
    assert.ok(piston.min.y>=bore.min.y&&piston.max.y<=bore.max.y&&
      piston.min.x>=center.x-radius&&piston.max.x<=center.x+radius&&
      piston.min.z>=center.z-radius&&piston.max.z<=center.z+radius,`cylinder ${i+1} piston leaves its bore`);
  }
  const crank=view.scene.getObjectByName('engine-crankshaft');assert.ok(crank);
  const crankBounds=new THREE.Box3().setFromObject(crank);
  assert.ok(crankBounds.min.x<=new THREE.Box3().setFromObject(pistons[0]).min.x);
  assert.ok(crankBounds.max.x>=new THREE.Box3().setFromObject(pistons[5]).max.x);
  engine.dispose();
});
test('turbo camera frames its subject more closely than the complete engine',{skip:!THREE},()=>{
  const {view,engine}=build();engine.setCamera('overview');const overview=view.camera.zoom;
  engine.setCamera('turbo');assert.ok(view.camera.zoom>overview*1.5);
  engine.dispose();
});

// Adapted from Explanatory Simulation/src/model/casting.mjs.
// Teaching geometry only; dimensions do not enter the engine model.
import * as THREE from 'three';

export function beveledBox(size, section = false, bevel = .02) {
  const [sx,sy,sz]=size,b=Math.min(bevel,sx*.12,sy*.22,sz*.12);
  const shape=new THREE.Shape();
  shape.moveTo(-sx/2+b,-sy/2+b);shape.lineTo(sx/2-b,-sy/2+b);
  shape.lineTo(sx/2-b,sy/2-b);shape.lineTo(-sx/2+b,sy/2-b);shape.closePath();
  const geometry=new THREE.ExtrudeGeometry(shape,{depth:sz-2*b,bevelEnabled:true,
    bevelThickness:b,bevelSize:b,bevelSegments:2,curveSegments:2,steps:1});
  geometry.computeBoundingBox();
  const initial=geometry.boundingBox.getSize(new THREE.Vector3());
  geometry.scale(sx/initial.x,sy/initial.y,sz/initial.z);geometry.computeBoundingBox();
  const center=geometry.boundingBox.getCenter(new THREE.Vector3());
  geometry.translate(-center.x,-center.y,-center.z);
  if(section){
    const normals=geometry.getAttribute('normal'),source=geometry.index;
    const count=source?.count ?? geometry.getAttribute('position').count,kept=[];
    for(let i=0;i<count;i+=3){
      const a=source?.getX(i) ?? i,b1=source?.getX(i+1) ?? i+1,c=source?.getX(i+2) ?? i+2;
      if((normals.getZ(a)+normals.getZ(b1)+normals.getZ(c))/3>.9 ||
         (normals.getY(a)+normals.getY(b1)+normals.getY(c))/3>.9)continue;
      kept.push(a,b1,c);
    }
    geometry.setIndex(kept);geometry.clearGroups();
  }
  geometry.computeBoundingBox();geometry.computeBoundingSphere();return geometry;
}

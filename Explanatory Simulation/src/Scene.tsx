import { useUI } from './useUI';
import { registerModal } from './modal-stack.mjs';
import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Maximize2, Minimize2, Pause, Play, RotateCcw, Focus, Eye } from 'lucide-react';
import { SceneClock } from './SceneClock';
import { EngineAssembly } from './EngineAssembly';
import { ThermalEnergyPaths, ThermalGuide } from './ThermalGuide';
import { VehicleAirflow } from './VehicleAirflow';
import { buildProjectStory } from './model/project-story.mjs';
import { TurboAssembly } from './TurboAssembly';
import { TURBO_CENTER, turboAnchors, turboFlowData } from './model/turbo-layout.mjs';
import { FlowGuide, flowSteps } from './FlowGuide';
import { StudioOperatingControls } from './StudioControls';
import { advanceVisualCycle } from './model/presentation.mjs';
import { STROKE_STATIONS, ignitionCommandDegrees, strokeAtDegrees, cylinderCycleDegrees, globalCycleForCylinder } from './model/engine-cycle.mjs';
import { cylinderX } from './model/engine-ports.mjs';
import type { Frame } from './types';
import { createSupraModel } from './model/supra.mjs';
import { routes, cylinderPose } from './model/layout.mjs';

type Point = [number, number, number];
type Props = { onViewport?:React.RefCallback<HTMLDivElement>; story?:React.ReactNode; onInspectTurbo?:()=>void; onInspectCylinder?:()=>void; onBackToVehicle?:()=>void; frame: any; running: boolean; speed: number; focus: string; onSelect: (id: string) => void; onLessonSelect?: (id: string) => void; layer: string; preview: boolean; road?: {time_s:number[]; grade_pct:number[]; speed_kmh:number[]}; time: number; stroke?: number; animateCycle?: boolean; studio?: boolean; onOperatingFrame?: (frame:Frame)=>void; onError?: (message:string)=>void };
const Clock=SceneClock;
type Appearance='solid'|'ghost'|'section';
type View='iso'|'front'|'side'|'top'|'focus'|'chamber';
type Visual={explode:number;appearance:Appearance;selectedPart:string;selectedCylinder:number;isolatedPart:string|null;onPartSelect:(part:string)=>void;onCylinderSelect:(index:number)=>void;onStroke:(id:string)=>void;flowStep:number;view:View;playing:boolean;rate:number;manual:number|null;orbit:boolean;phaseOutput:React.RefObject<HTMLOutputElement|null>;phaseInput:React.RefObject<HTMLInputElement|null>;strokeOutput:React.RefObject<HTMLOutputElement|null>};
const Presentation=createContext<Visual|null>(null);
const partInfo:Record<string,{name:string;hint:string;anchor:Point}>={
 crank:{name:'عمود المرفق',hint:'يحوّل حركة المكابس صعودًا وهبوطًا إلى دوران.',anchor:[1.49,.59,-.06]},
 piston:{name:'المكابس والأذرع',hint:'ضغط الاحتراق يدفع المكبس؛ والذراع ينقل القوة إلى العمود.',anchor:[1.49,.86,-.06]},
 head:{name:'رأس المحرك',hint:'يضم الصمامات وممرات دخول الهواء وخروج العادم.',anchor:[1.49,1.06,-.06]},
 spark:{name:'شمعات الإشعال',hint:'تقديم الشرارة يغيّر توقيت الاحتراق في حسابات النموذج.',anchor:[1.49,1.115,-.06]},
 block:{name:'كتلة المحرك',hint:'تحتوي الأسطوانات؛ وحرارتها عقدة مجمّعة في النموذج.',anchor:[1.49,.72,-.06]},
 pan:{name:'حوض الزيت',hint:'يجمع الزيت؛ ويُمثّل حراريًا بحالة واحدة في النموذج.',anchor:[1.49,.5,-.06]},
 intake:{name:'صمامات السحب',hint:'تدخل الشحنة في شوط السحب. حركة الصمام هنا تعليمية.',anchor:[1.49,1.075,0]},
 exhaust:{name:'صمامات العادم',hint:'تخرج الغازات في شوط العادم. التدفق هنا توضيحي.',anchor:[1.49,1.075,-.1]},
 injector:{name:'البخاخ والوقود',hint:'البخاخ علامة تعليمية مستقلة عن شمعة الإشعال. لامدا أقل من 1 تعني وقودًا أكثر لكل وحدة هواء.',anchor:[1.49,1.13,-.136]},
};
const C = { air:'#339cae', exhaust:'#c97147', coolant:'#398faf', oil:'#c79a47', metal:'#8b9895', dark:'#344947', selected:'#248a78' };
const {air:AIR,charge:CHARGE,exhaust:EXHAUST,tail:TAIL,coolant:COOLANT,oil:OIL}=routes;
const clamp = (v:number, a:number, b:number) => Math.max(a,Math.min(b,v));
const value = (f:any,k:string, fallback=0) => typeof f?.[k]==='number' && Number.isFinite(f[k]) ? f[k] : fallback;
const click = (id:string, fn:Props['onSelect']) => (e:{stopPropagation:()=>void}) => { e.stopPropagation();fn(id); };
const heat = (v:any) => typeof v==='number' && Number.isFinite(v) ? new THREE.Color().setHSL(.56-clamp((v-290)/650,0,.5),.48,.5) : new THREE.Color(C.metal);

function BoxPart({position, size, color, onClick, opacity=1,unlit=false}:{position:Point;size:Point;color:THREE.ColorRepresentation;onClick?:any;opacity?:number;unlit?:boolean}) {
  const { ui } = useUI();

  return <mesh position={position} onClick={onClick} castShadow><boxGeometry args={size}/>{unlit?<meshBasicMaterial color={color}/>:<meshStandardMaterial color={color} metalness={.32} roughness={.42} transparent={opacity<1} opacity={opacity} depthWrite={opacity===1}/>}</mesh>;
}
function Pipe({points,color,active,onClick,radius=.034}:{points:Point[];color:string;active:boolean;onClick?:any;radius?:number}) {
  const curve=useMemo(()=>new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)),false,'centripetal'),[points]);
  const geometry=useMemo(()=>new THREE.TubeGeometry(curve,48,radius,8,false),[curve,radius]);
  useEffect(()=>()=>geometry.dispose(),[geometry]);
  return <mesh geometry={geometry} onClick={onClick}><meshStandardMaterial color={active?color:C.metal} roughness={.4} transparent={!active} opacity={active?1:.25} depthWrite={active}/></mesh>;
}
function Flow({points,color,density=1}:{points:Point[];color:string;density?:number}) {
  const { ui } = useUI();

  const clock=useContext(Clock); const dots=useRef<(THREE.Mesh|null)[]>([]);
  const curve=useMemo(()=>new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)),false,'centripetal'),[points]);
  useFrame(()=>dots.current.forEach((m,i)=>{if(m){m.position.copy(curve.getPoint((clock.time*.16+i/6)%1));m.scale.setScalar(density);}}));
  return <group>{Array.from({length:6},(_,i)=><mesh key={i} ref={m=>{dots.current[i]=m;}}><sphereGeometry args={[.041,10,8]}/><meshBasicMaterial color={color}/></mesh>)}</group>;
}
function Engine({frame,onSelect,detail}:{frame:any;detail:boolean;onSelect:Props['onSelect']}) {
  const v=useContext(Presentation);
  return <EngineAssembly frame={frame} study={detail && !!v} crossSection={detail && v?.view==='chamber'} onSelect={onSelect} onPartSelect={v?.onPartSelect} onCylinderSelect={v?.onCylinderSelect} selectedPart={v?.selectedPart} selectedCylinder={v?.selectedCylinder} explode={v?.explode||0} appearance={v?.appearance||'ghost'} isolatedPart={v?.isolatedPart}/>;
}
function Systems(p:Props) {
  const { ui } = useUI();

  const air=p.layer==='turbo'||!!p.studio&&['vehicle','agent'].includes(p.layer);const thermal=p.layer==='thermal';const density=clamp(value(p.frame,'map_kpa',101)/101*.9,.7,1.7);
  return <group><Engine frame={p.frame} detail={false} onSelect={p.onSelect}/>
    <VehicleAirflow frame={p.frame} onSelect={p.onSelect} onInspectTurbo={()=>p.onInspectTurbo?.()} onInspectCylinder={p.onInspectCylinder} active={air||thermal} showLabels={p.layer!=='agent'}/>
    {[[COOLANT,C.coolant,'t_block'],[OIL,C.oil,'t_oil']].map(([pts,color,id],i)=><group key={i}><Pipe points={pts as Point[]} color={color as string} active={thermal} onClick={click(id as string,p.onSelect)}/>{thermal&&<Flow points={pts as Point[]} color={color as string}/>}</group>)}
    <group onClick={click('fan_duty',p.onSelect)}><BoxPart position={[2.82,.83,0]} size={[.12,.43,1.32]} color={thermal?C.coolant:C.dark}/>{Array.from({length:7},(_,i)=><BoxPart key={i} position={[2.895,.83,-.55+i*.183]} size={[.025,.39,.012]} color="#9cbbb5"/>)}</group>
    {thermal&&<ThermalEnergyPaths frame={p.frame} focus={p.focus} onSelect={p.onSelect}/>}
    <group onClick={click('gear',p.onSelect)}><BoxPart position={[.08,.6,-.06]} size={[.7,.31,.48]} color={C.dark}/><mesh position={[-1.03,.47,-.06]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.028,.028,1.73,12]}/><meshStandardMaterial color={C.metal} metalness={.65}/></mesh><BoxPart position={[-2.12,.48,-.06]} size={[.25,.22,.32]} color={C.dark}/><mesh position={[-2.12,.5,0]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.025,.025,2.4,12]}/><meshStandardMaterial color={C.metal} metalness={.6}/></mesh></group>
  </group>;
}
function Car({cutaway,...p}:Props&{cutaway:boolean}) {
  const { ui } = useUI();

  const model=useMemo(()=>createSupraModel(),[]);const clock=useContext(Clock);
  useEffect(()=>{model.root.traverse((o:any)=>{if(!o.isMesh)return;if(o.userData.component==='body-shell'||o.userData.component==='glazing'){o.material.transparent=cutaway;o.material.opacity=cutaway?(o.userData.component==='glazing'?.045:.075):1;o.material.depthWrite=!cutaway;o.castShadow=!cutaway;o.material.needsUpdate=true;o.raycast=cutaway?()=>{}:THREE.Mesh.prototype.raycast;}});},[cutaway,model]);
  useEffect(()=>()=>{const g=new Set<THREE.BufferGeometry>();const m=new Set<THREE.Material>();model.root.traverse((o:any)=>{if(o.isMesh){g.add(o.geometry);(Array.isArray(o.material)?o.material:[o.material]).forEach((x:THREE.Material)=>m.add(x));}});g.forEach(x=>x.dispose());m.forEach(x=>x.dispose());},[model]);
  useFrame(()=>model.wheels.forEach(w=>{w.rotation.z=-clock.time*value(p.frame,'speed_kmh')/3.6/.62/8;}));
  return <group rotation={[0,0,Math.atan(value(p.frame,'grade_pct')/100)]}>
    <primitive object={model.root} dispose={null} onClick={(e:any)=>{e.stopPropagation();let o=e.object;let id='engine';while(o){if(o.userData.component==='wheel'){id='gear';break;}o=o.parent;}p.onSelect(id);}}/>
    {cutaway&&<Systems {...p}/>}
  </group>;
}
function CameraRig({layer,reset,zoomRequest,reduced,studio,visual}:{layer:string;reset:number;zoomRequest:{seq:number;factor:number};reduced:boolean;studio?:boolean;visual:Visual}) {
  const {camera,size}=useThree();const controls=useRef<any>(null);const moving=useRef(true);
  const view=useMemo(()=>{
    const engine=layer==='engine';const turbo=studio&&layer==='turbo';const focused=(engine||turbo)&&visual.view==='focus';
    const cylinderFocus=engine&&(visual.view==='chamber'||(focused||visual.view==='side')&&['intake','exhaust','injector','piston','spark'].includes(visual.selectedPart));
    const anchor=studio&&layer==='agent'?[2.2,.73,0]:turbo?(focused?(turboAnchors[visual.selectedPart]||TURBO_CENTER):TURBO_CENTER):cylinderFocus?[cylinderX(visual.selectedCylinder),.88,-.06]:focused?(partInfo[visual.selectedPart]?.anchor||[1.49,.82,-.06]):engine?[1.49,.82,-.06]:layer==='turbo'?[1.83,.82,.15]:layer==='thermal'?[1.35,.75,0]:[0,.73,0];
    const target=new THREE.Vector3(...anchor as Point);
    if(engine)target.y+=visual.explode*.08;
    const direction=new THREE.Vector3(...(visual.view==='chamber'?[7,.8,.02]:visual.view==='front'?[7,.9,.03]:visual.view==='side'?[.03,1,7]:visual.view==='top'?[.03,7,1.2]:engine?[3.8,3.1,5.4]:[7.8,5.7,8.9]) as Point);
    const extent=studio&&layer==='agent'?[14,7.8]:turbo?(size.width<700?[2.1+visual.explode*.5,1.8]:[3.3+visual.explode*.5,2.2]):engine?(visual.view==='chamber'?[.88+visual.explode*.2,.88+visual.explode*.3]:cylinderFocus?[1.15+visual.explode*.6,1.05+visual.explode*.45]:[2.35+visual.explode*.3,1.6+visual.explode*.6]):layer==='turbo'?[4.5,3.1]:layer==='thermal'?[5.5,3.7]:[9.7,5.6];
    const reserved=studio&&size.width>700?(layer==='agent'?350:['engine','turbo','vehicle'].includes(layer)?270:0):0;
    const top=studio?(engine&&size.width>700?245:120):60;const bottom=studio?(size.width<700?10:layer==='vehicle'?310:engine?15:turbo?265:layer==='agent'?175:210):80;
    const zoom=Math.min((size.width-reserved-30)/extent[0],(size.height-top-bottom)/extent[1]);
    if(reserved){const right=new THREE.Vector3().crossVectors(direction,new THREE.Vector3(0,1,0)).normalize().negate();target.addScaledVector(right,reserved/(2*Math.max(20,zoom)));}
    if(studio){const normal=direction.clone().normalize();const up=new THREE.Vector3(0,1,0).addScaledVector(normal,-normal.y).normalize();target.addScaledVector(up,(top-bottom)/(2*Math.max(20,zoom)));}
    return {target,position:target.clone().add(direction),zoom:Math.max(20,zoom)};
  },[layer,size.width,size.height,studio,visual.view,visual.explode,visual.selectedPart,visual.selectedCylinder]);
  useEffect(()=>{moving.current=true;},[view,reset]);
  useEffect(()=>{if(!zoomRequest.seq)return;moving.current=false;const c=camera as THREE.OrthographicCamera;c.zoom=clamp(c.zoom*zoomRequest.factor,view.zoom*.65,view.zoom*3.4);c.updateProjectionMatrix();},[zoomRequest]);
  useFrame((_,dt)=>{if(!moving.current||!controls.current)return;const a=reduced?1:1-Math.exp(-dt*4);camera.position.lerp(view.position,a);controls.current.target.lerp(view.target,a);const c=camera as THREE.OrthographicCamera;c.zoom=THREE.MathUtils.lerp(c.zoom,view.zoom,a);c.updateProjectionMatrix();controls.current.update();if(camera.position.distanceTo(view.position)<.008&&Math.abs(c.zoom-view.zoom)<.05)moving.current=false;});
  return <OrbitControls ref={controls} makeDefault enablePan enableDamping autoRotate={visual.orbit&&!reduced} autoRotateSpeed={.45} minZoom={view.zoom*.65} maxZoom={view.zoom*3.4} minPolarAngle={.15} maxPolarAngle={Math.PI/2.06} onStart={()=>{moving.current=false;}}/>;
}
function World({cutaway,demo,reduced,reset,zoomRequest,visual,...p}:Props&{cutaway:boolean;demo:boolean;reduced:boolean;reset:number;zoomRequest:{seq:number;factor:number};visual:Visual}) {
  const { ui, uiTemplate } = useUI();

  const clock=useMemo(()=>({time:0,cycle:0}),[]);const seen=useRef({time:-1,at:0});const lab=useRef(0);const previousStroke=useRef('');
  useFrame((state,dt)=>{
    if(p.studio){
      if(visual.playing&&!reduced)clock.time+=Math.min(.1,dt)*visual.rate;
      clock.cycle=visual.manual==null?advanceVisualCycle(clock.cycle,dt,value(p.frame,'rpm'),visual.rate,visual.playing&&!reduced):globalCycleForCylinder(visual.manual,visual.selectedCylinder);
      const chosenAngle=visual.manual??cylinderCycleDegrees(clock.cycle,visual.selectedCylinder);
      if(visual.phaseOutput.current)visual.phaseOutput.current.textContent=`${Math.round(chosenAngle)}°`;
      if(visual.phaseInput.current)visual.phaseInput.current.value=String(Math.round(chosenAngle));
      const stroke=strokeAtDegrees(chosenAngle);
      if(visual.strokeOutput.current)visual.strokeOutput.current.textContent=uiTemplate("أسطوانة {0} · {1} · {2}", "Cylinder {0} · {1} · {2}", visual.selectedCylinder+1, stroke.name, stroke.hint);
      if(p.layer==='engine'&&previousStroke.current!==stroke.id){previousStroke.current=stroke.id;visual.onStroke(stroke.id);}
    } else {
      const t=value(p.frame,'time_s',p.time);if(seen.current.time!==t)seen.current={time:t,at:state.clock.elapsedTime};if((p.animateCycle||demo)&&!reduced)lab.current+=dt;
      clock.time=(p.animateCycle||demo)?lab.current:t+(p.running&&!reduced?Math.min((state.clock.elapsedTime-seen.current.at)*p.speed,.75):0);clock.cycle=p.stroke==null?(clock.time*value(p.frame,'rpm',1500)/120/18)%1:(p.stroke+.5)/4;
    }
  });
  const engine=p.layer==='engine';const slope=Math.atan(value(p.frame,'grade_pct')/100);
  return <Presentation.Provider value={visual}><Clock.Provider value={clock}>
    <color attach="background" args={[p.studio?'#090e15':'#edf0e8']}/><ambientLight intensity={p.studio?.22:1.1}/><hemisphereLight args={['#dce7f4',p.studio?'#202934':'#89998d',p.studio?.5:1.3]}/><directionalLight position={[2,7,4]} color="#fff0d3" intensity={p.studio?2.4:3.6} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048}/><directionalLight position={[-3,3,-4]} color="#9cb5d6" intensity={p.studio?1.6:2.5}/><directionalLight position={[4,1,-2]} color="#f4a363" intensity={p.studio?.75:1.3}/>
    <mesh position={[0,-.47,0]} rotation={[-Math.PI/2,0,0]} receiveShadow><planeGeometry args={[30,30]}/>{p.studio?<meshBasicMaterial color="#101720"/>:<meshStandardMaterial color="#e1e7dc" roughness={.6}/>}</mesh>
    {p.studio&&<gridHelper args={[14,28,'#263342','#192431']} position={[0,-.465,0]}/>}
    {p.studio&&p.layer==='turbo'?<><TurboAssembly frame={p.frame} appearance={visual.appearance} explode={visual.explode} selectedPart={visual.selectedPart} isolatedPart={visual.isolatedPart} onPartSelect={visual.onPartSelect} onSelect={p.onSelect} flowStep={visual.flowStep}/><BoxPart position={[0,.05,0]} size={[2.6,.08,1.8]} unlit color="#1d2834"/></>:engine?<><Engine frame={p.frame} detail onSelect={p.onSelect}/><BoxPart position={[1.49,.13,-.06]} size={[1.95,.06,.95]} unlit={p.studio} color={p.studio?'#1d2834':'#d3dcd0'}/><BoxPart position={[1.49,.06,-.06]} size={[1.82,.08,.85]} unlit={p.studio} color={p.studio?'#101722':'#becab9'}/></>:<><group rotation={[0,0,slope]} onClick={click('grade',p.onSelect)}><BoxPart position={[0,-.065,0]} size={[12,.12,3.45]} color={p.studio?'#263341':'#61726b'}/>{[-1.53,1.53].map(z=><Line key={z} points={[[-6,.001,z],[6,.001,z]]} color="#e0e6d9" lineWidth={2}/>)}<Line points={[[-6,.005,0],[6,.005,0]]} color="#e1dbc2" dashed dashSize={.4} gapSize={.36} lineWidth={2}/></group><Car {...p} cutaway={cutaway}/></>}
    {p.studio&&p.layer==='agent'&&<RoadAhead {...p}/>}
    <CameraRig layer={p.layer} reset={reset} zoomRequest={zoomRequest} reduced={reduced} studio={p.studio} visual={visual}/>
  </Clock.Provider></Presentation.Provider>;
}
function RoadAhead(p:Props){
  const { number, ui } = useUI();

  const story=buildProjectStory(p.frame,{preview:p.preview,road:p.road,time:p.time});
  return <group>{story.previewSlots.map((slot,i)=>{
    const x=3.85+i*1.32;return <group key={slot.seconds}><BoxPart position={[x,.12,0]} size={[1.2,.035,2.3]} color={p.preview?'#253f4c':'#252d38'} unlit/>
      <Html position={[x,.55,-1.3]} center zIndexRange={[2,0]} style={{left:0}}><button className="road-future-label" onClick={()=>p.onSelect(`preview_${slot.seconds}s`)}><bdi dir="ltr">+{ui(slot.seconds)}s</bdi><strong dir="ltr">{ui(p.preview?`${number(slot.gradePct,1)}%`:'محجوب')}</strong></button></Html></group>;
  })}<Line points={[[3.25,.15,0],[8.5,.15,0]]} color={p.preview?'#73bdcc':'#4c5969'} lineWidth={2} dashed/></group>;
}
export default function Scene(p:Props) {
  const { number, ui, uiTemplate } = useUI();

  const [body,setBody]=useState(false);const [demo,setDemo]=useState(false);const [reset,setReset]=useState(0);const [zoomRequest,setZoomRequest]=useState({seq:0,factor:1});
  const [appearance,setAppearance]=useState<Appearance>('section');const [explode,setExplode]=useState(0);const [selectedPart,setSelectedPart]=useState('crank');const [selectedCylinder,setSelectedCylinder]=useState(0);const [isolatedPart,setIsolatedPart]=useState<string|null>(null);const [view,setView]=useState<View>('iso');
  const [flowStep,setFlowStep]=useState(-1);
  const [thermalNode,setThermalNode]=useState('t_turb');
  useEffect(()=>{if(['t_block','t_oil','t_turb'].includes(p.focus))setThermalNode(p.focus);},[p.focus]);
  const thermalFocus=['t_block','t_oil','t_turb'].includes(p.focus)?p.focus:thermalNode;
  const [playing,setPlaying]=useState(true);const [rate,setRate]=useState(.5);const [manual,setManual]=useState<number|null>(null);const [orbit,setOrbit]=useState(false);const [expanded,setExpanded]=useState(false);
  const [activeStroke,setActiveStroke]=useState('intake');
  const lessonStage=useRef<HTMLDivElement>(null);
  const phaseOutput=useRef<HTMLOutputElement>(null);const phaseInput=useRef<HTMLInputElement>(null);const strokeOutput=useRef<HTMLOutputElement>(null);const sceneElement=useRef<HTMLElement>(null);const savedVehicleView=useRef<View>('iso');
  useEffect(()=>{setDemo(false);setIsolatedPart(null);setView(p.layer==='engine'?'focus':p.layer==='vehicle'?savedVehicleView.current:'iso');setExplode(0);setSelectedPart(p.layer==='turbo'?'overview':p.layer==='engine'?'intake':'crank');setSelectedCylinder(0);setFlowStep(-1);setManual(p.layer==='engine'?0:null);setPlaying(p.layer!=='engine');},[p.layer]);
  useEffect(()=>{
    if(!expanded || !sceneElement.current)return;
    return registerModal(document, { element: sceneElement.current, onClose: () => setExpanded(false) });
  },[expanded]);
  const reduced=typeof window!=='undefined'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const engine=p.layer==='engine';const turbo=!!p.studio&&p.layer==='turbo';const cutaway=p.studio?appearance!=='solid':body||p.layer!=='vehicle';
  const choosePart=(part:string)=>{if(turbo)setFlowStep(['compressor','compressor-housing'].includes(part)?1:part==='turbo-shaft'?2:3);setSelectedPart(part);setIsolatedPart(null);setView(old=>old==='chamber'?'chamber':'focus');};
  const visual:Visual={explode:engine||turbo?explode:0,appearance,selectedPart,selectedCylinder,isolatedPart,onPartSelect:choosePart,onCylinderSelect:setSelectedCylinder,onStroke:setActiveStroke,flowStep,view,playing,rate,manual,orbit,phaseOutput,phaseInput,strokeOutput};
  const sparkCommand=ignitionCommandDegrees(p.frame?.spark);
  const currentStroke=STROKE_STATIONS.find(stroke=>stroke.id===activeStroke)||STROKE_STATIONS[0];
  const keepLessonVisible=()=>{
    if(!window.matchMedia('(max-width:700px)').matches)return;
    const stage=lessonStage.current;
    if(stage){const rect=stage.getBoundingClientRect();if(rect.top<0||rect.bottom>window.innerHeight)stage.scrollIntoView({block:'start'});}
  };
  const lessonSelect=(concept:string)=>{p.onLessonSelect?.(concept);keepLessonVisible();};
  const restartCycle=()=>{setManual(0);setPlaying(false);setActiveStroke('intake');setIsolatedPart(null);choosePart('intake');lessonSelect('air');};
  const cycleControls=<div className="studio-cycle-controls">
    <button className="studio-play" onClick={()=>{setManual(null);setPlaying(!playing);}}>{playing?<Pause size={16}/>:<Play size={16}/>} {ui(playing?'أوقف الحركة':'حرّك الآلية')}</button>
    <select aria-label={ui("سرعة الحركة التعليمية")} value={rate} onChange={e=>setRate(+e.target.value)}><option value={.15}>{ui("بطيئة جدًا")}</option><option value={.5}>{ui("بطيئة")}</option><option value={1}>{ui("عادية")}</option></select>
    {engine&&<><button onClick={restartCycle}>{ui("إعادة بداية الدورة")}</button><label className="studio-crank-angle">{ui("افحص الدورة")}<input ref={phaseInput} aria-label={ui("زاوية دورة المحرك التعليمية")} type="range" min={0} max={720} step={1} defaultValue={0} onChange={e=>{setManual(+e.target.value);setPlaying(false);}}/><output ref={phaseOutput} dir="ltr">0°</output></label></>}
  </div>;
  const inspectCylinder=()=>{savedVehicleView.current=view;p.onInspectCylinder?.();};
  const flow=turboFlowData(p.frame);
  const metrics=turbo?[['تدفق الهواء',flow.air,'g/s'],['تدفق العادم',flow.exhaust,'g/s'],['غاز العادم',p.frame?.egt_c,'°C']]:p.layer==='thermal'?[['حرارة التوربين',typeof p.frame?.t_turb==='number'?p.frame.t_turb-273.15:null,'°C'],['حرارة الزيت',typeof p.frame?.t_oil==='number'?p.frame.t_oil-273.15:null,'°C'],['حرارة المحرك',typeof p.frame?.t_block==='number'?p.frame.t_block-273.15:null,'°C']]:[['دوران المحرك',p.frame?.rpm,'rpm'],['ضغط السحب',p.frame?.map_kpa,'kPa abs'],['غاز العادم',p.frame?.egt_c,'°C']];
  const previewTime=value(p.frame,'input_time_s',p.time);
  const horizons=[2,5,15,30].map(h=>{const i=p.road?.time_s.findIndex(t=>t>=previewTime+h);return {h,grade:!p.preview?0:i!=null&&p.road?.time_s.length?p.road.grade_pct[i<0?p.road.time_s.length-1:i]:undefined};});
  return <section ref={sceneElement} tabIndex={expanded?-1:undefined} className={`model-view ${engine?'engine-detail':''} ${p.layer==='thermal'&&!p.studio?'thermal-detail':''} ${turbo?'turbo-detail':''} ${p.layer==='vehicle'?'vehicle-detail':''} ${p.layer==='agent'?'project-detail':''} ${p.studio?'studio-view':''} ${expanded?'studio-expanded':''}`} aria-label={ui("نموذج السوبرا التفاعلي")} role={expanded?'dialog':undefined} aria-modal={expanded||undefined}>
    <div ref={lessonStage} className={engine&&p.studio?'engine-learning-stage':'studio-render-surface'}>
      <div ref={p.onViewport} data-model-viewport tabIndex={-1} role="group" aria-label={uiTemplate('منطقة عرض النموذج', 'Model viewing area')} className={engine&&p.studio?'engine-learning-canvas':'studio-world'}><Canvas orthographic shadows dpr={[1,1.7]} camera={{position:[7.8,6.43,8.9],zoom:65,near:.1,far:100}} gl={{antialias:true}}><World {...p} focus={p.layer==='thermal'?thermalFocus:p.focus} onInspectCylinder={inspectCylinder} cutaway={cutaway} demo={demo} reduced={reduced} reset={reset} zoomRequest={zoomRequest} visual={visual}/></Canvas></div>
      {engine&&p.studio&&<div className="engine-study">
        <div className="engine-study__head"><strong>{ui("درس الأسطوانة ")}{ui(selectedCylinder+1)}</strong><div><button onClick={()=>p.onSelect('four_stroke')}>{ui("شرح الدورة")}</button><button onClick={()=>p.onBackToVehicle?.()}>{ui("العودة إلى السيارة")}</button></div></div>
        <div className="engine-cylinder-choices" aria-label={ui("اختر أسطوانة")}>{Array.from({length:6},(_,i)=><button key={i} aria-label={ui(uiTemplate("أسطوانة {0}", "Cylinder {0}", i+1))} aria-pressed={selectedCylinder===i} className={selectedCylinder===i?'active':''} onClick={()=>{setSelectedCylinder(i);setIsolatedPart(null);setView(old=>old==='chamber'?'chamber':'focus');lessonSelect(activeStroke==='power'?'spark':activeStroke==='exhaust'?'egt':activeStroke==='compression'?'four_stroke':'air');}}><span>{ui("أسطوانة ")}</span><bdi>{ui(i+1)}</bdi></button>)}</div>
        <div className="engine-stroke-choices" aria-label={ui("محطات الدورة التعليمية")}>{STROKE_STATIONS.map(stroke=><button key={stroke.id} aria-pressed={activeStroke===stroke.id} className={activeStroke===stroke.id?'active':''} onClick={()=>{setManual(stroke.angle);setPlaying(false);choosePart(stroke.id==='intake'?'intake':stroke.id==='exhaust'?'exhaust':stroke.id==='power'?'spark':'piston');lessonSelect(stroke.id==='intake'?'air':stroke.id==='exhaust'?'egt':stroke.id==='power'?'spark':'four_stroke');}}>{ui(stroke.name)}</button>)}</div>
        <div className="engine-ignition-cue"><button disabled={sparkCommand===null} onClick={()=>{if(sparkCommand===null)return;setManual(sparkCommand);setPlaying(false);choosePart('spark');lessonSelect('spark');}}>{ui("لحظة الشرارة")}</button> <span>{sparkCommand===null?ui('توقيت الشرارة غير متاح'):uiTemplate('أمر الإشعال عند {0}° · {1}', 'Ignition command at {0}° · {1}', sparkCommand, p.frame.spark===0?ui('عند النقطة الميتة العليا'):p.frame.spark>0?uiTemplate('{0}° قبل النقطة الميتة العليا', '{0}° before top dead center', p.frame.spark):uiTemplate('{0}° بعد النقطة الميتة العليا', '{0}° after top dead center', Math.abs(p.frame.spark)))}</span><small> {ui(" الومضة 8° توضيحية؛ يبدأ الاحتراق ثم يستمر بعد انطفائها. النقطة الميتة العليا للضغط عند 360°.")}</small></div>
        <output ref={strokeOutput} className="engine-stroke-description" aria-label={ui("الشوط الحالي")}>{ui("أسطوانة ")}{ui(selectedCylinder+1)} {ui(" · سحب · تدخل الشحنة وينزل المكبس.")}</output>
        <div className="engine-valve-status" aria-label={ui("حالة الصمامين وحركة المكبس")}><span className="air-state">{ui("السحب: ")}{ui(currentStroke.intakeOpen?'مفتوح':'مغلق')}</span><span className="exhaust-state">{ui("العادم: ")}{ui(currentStroke.exhaustOpen?'مفتوح':'مغلق')}</span><span>{ui(currentStroke.pistonDirection==='up'?'↑ المكبس يصعد':'↓ المكبس ينزل')}</span></div>
        {ui(cycleControls)}
        {explode>0?<p className="engine-disassembly-note">{ui("الرأس مفصول للتعلّم؛ التدفق داخل الحجرة متوقف. أعد التجميع لتتبع الشحنة.")}</p>:<p>{ui("المسار الوردي: وقود من مسطرة التغذية → البخاخ → منفذ السحب → الشحنة داخل الحجرة. الزيت بلون بني. مسار الحقن وتوقيته رسم تعليمي، لا يصفان هندسة B58 المصنعية. الشمعة تبدأ الاحتراق.")}</p>}
      </div>}
    </div>
    <div className="model-values" aria-label={ui("قيم النموذج الحالية")}>{metrics.map(([label,v,u])=><div key={label as string}><small>{ui(label)}</small><strong dir="ltr"><bdi>{ui(number(v,label==='دوران المحرك'?0:1))}</bdi><span dir="ltr"> {ui(u)}</span></strong></div>)}</div>
    {p.layer==='agent'&&!p.studio&&<div className="model-preview" aria-label={ui("ميل الطريق القادم")}>{horizons.map(({h,grade})=><button key={h} onClick={()=>p.onSelect('preview')}><small>{ui("بعد ")}<bdi>{ui(h)}</bdi> {ui(" ث")}</small><strong><bdi>{ui(number(grade,1))}%</bdi></strong></button>)}</div>}
    {!p.studio&&p.layer==='thermal'&&<ThermalGuide frame={p.frame} focus={thermalFocus} onSelect={p.onSelect}/>}
    {p.studio?<>
      <div className="studio-scene-tools"><button aria-label={ui(expanded?'إغلاق العرض الموسّع':'توسيع المختبر')} title={ui(expanded?'إغلاق العرض الموسّع':'توسيع المختبر')} onClick={()=>setExpanded(!expanded)}>{expanded?<Minimize2 size={18}/>:<Maximize2 size={18}/>}</button><button aria-label={ui("تكبير النموذج")} onClick={()=>setZoomRequest(z=>({seq:z.seq+1,factor:1.22}))}>＋</button><button aria-label={ui("تصغير النموذج")} onClick={()=>setZoomRequest(z=>({seq:z.seq+1,factor:1/1.22}))}>−</button><button aria-label={ui("إعادة المنظور")} onClick={()=>{setView('iso');setReset(r=>r+1);}}><RotateCcw size={17}/></button></div>
      <div className="studio-view-presets" aria-label={ui("زوايا الفحص")}>{([['iso','منظور حر'],['front','أمامي'],['side','جانبي'],['top','علوي']] as const).map(([id,label])=><button key={id} className={view===id?'active':''} onClick={()=>{setView(id);if(p.layer==='vehicle')savedVehicleView.current=id;}}>{ui(label)}</button>)}{engine&&<button className={view==='chamber'?'active':''} onClick={()=>{setAppearance('section');setIsolatedPart(null);setView('chamber');keepLessonVisible();}}>{ui("مقطع الأسطوانة")}</button>}<button className={orbit?'active':''} onClick={()=>setOrbit(!orbit)}>{ui("تدوير تلقائي")}</button></div>
      {(engine||turbo)&&<div className="studio-part-card"><span className="studio-kicker">{ui("الجزء المختار")}</span><h2>{ui(turbo?(selectedPart==='compressor-housing'?'غلاف الضاغط':selectedPart==='turbo-housing'?'غلاف التوربين':flowStep<0?'التيربو: مساران وعمود واحد':flowSteps[flowStep].title):partInfo[selectedPart]?.name)}</h2><p>{ui(turbo?(selectedPart==='compressor-housing'?'يوجّه الهواء من مركز الضاغط إلى المخرج المحيطي. ضغط السحب مدخل مستقل لنقطة التشغيل.':selectedPart==='turbo-housing'?'يحيط الغلاف بالدوّار ويوجّه الغاز. حرارة الغلاف عقدة حرارية مستقلة؛ لا نستنتجها من حرارة غاز العادم.':flowStep<0?'الهواء الأزرق يدخل الضاغط؛ والعادم البرتقالي يدير التوربين. العمود يربط الدوّارين دون خلط الغازين.':flowSteps[flowStep].hint):partInfo[selectedPart]?.hint)}</p><div><button disabled={turbo&&flowStep<0} onClick={()=>setView('focus')}><Focus size={14}/>{ui("ركّز عليه")}</button><button disabled={turbo&&flowStep<0} onClick={()=>{setIsolatedPart(isolatedPart?null:selectedPart);setView(isolatedPart?'iso':'focus');}}><Eye size={14}/>{ui(isolatedPart?'عرض التجميع':'عزل الجزء')}</button></div></div>}
      {p.onOperatingFrame&&<StudioOperatingControls active={engine||p.layer==='turbo'||p.layer==='vehicle'} onFrame={p.onOperatingFrame} onError={p.onError}/>}
      {p.story&&<div className="studio-project-panel">{ui(p.story)}</div>}
      <div className="studio-bottom">
        {p.layer==='thermal'&&<ThermalGuide frame={p.frame} focus={thermalFocus} onSelect={p.onSelect}/>}
        {p.layer==='vehicle'&&<div className="vehicle-path-guide"><strong>{ui("اتبع الهواء والعادم")}</strong><p><span>{ui("هواء خارجي → فلتر → ضاغط التيربو → مبرد الشحنة → مجمع السحب → منافذ الرأس → الأسطوانات")}</span><br/><span>{ui("الأسطوانات → منافذ العادم → التوربين → أنبوب العادم → خارج السيارة")}</span></p><div className="vehicle-path-actions"><button onClick={inspectCylinder}>{ui("اتبع أسطوانة واحدة")}</button><button onClick={()=>p.onInspectTurbo?.()}>{ui("افحص التيربو مكبّرًا")}</button></div><small>{ui("الأسهم وفروع الأسطوانات رسم تعليمي؛ تدفق الهواء والعادم الكلي من النموذج. تجربة نقطة المحرك مستقلة عن جلسة الطريق.")}</small></div>}
        {p.layer==='agent'&&<p className="project-scene-note">{ui("أمام السيارة: خانات المستقبل التي تصل للمشرف. التباعد بين الخانات رسم توضيحي؛ الآفاق بالثواني وليست مسافات مقاسة.")}</p>}
        {turbo&&<FlowGuide frame={p.frame} step={flowStep} onStep={index=>{if(index<0){setFlowStep(-1);setSelectedPart('overview');setIsolatedPart(null);setView('iso');p.onSelect('turbocharger');}else{choosePart(flowSteps[index].part);setFlowStep(index);p.onSelect(flowSteps[index].concept);}}}/>}
        {engine&&<div className="studio-part-shortcuts" aria-label={ui("اختيار جزء من المحرك")}>{['intake','injector','spark','exhaust','piston','crank','head','block'].map(id=><button key={id} className={selectedPart===id?'active':''} onClick={()=>{choosePart(id);p.onSelect(({intake:'air',injector:'fuel',spark:'spark',exhaust:'egt',piston:'four_stroke',crank:'engine_torque',head:'engine',block:'t_block'} as Record<string,string>)[id]);}}>{ui(partInfo[id].name)}</button>)}</div>}
        <div className="studio-display-controls"><div className="studio-segment" aria-label={ui("طريقة عرض الأجزاء")}>{([['solid','كامل'],['ghost','شفاف'],['section','مقطع']] as const).map(([id,label])=><button key={id} className={appearance===id?'active':''} onClick={()=>setAppearance(id)}>{ui(label)}</button>)}</div>{(engine||turbo)&&<label className="studio-explode">{ui("تفكيك تعليمي")}<input aria-label={ui(turbo?"تفكيك أجزاء التيربو":"تفكيك أجزاء المحرك")} type="range" min={0} max={1} step={.01} value={explode} onChange={e=>{setExplode(+e.target.value);setPlaying(false);if(engine)setManual(0);setIsolatedPart(null);setView('iso');}}/><output><bdi>{ui(Math.round(explode*100))}%</bdi></output></label>}<button onClick={()=>{setExplode(0);setIsolatedPart(null);setView('iso');setReset(r=>r+1);}}>{ui("إعادة التجميع")}</button></div>
        {ui(!engine&&cycleControls)}
        <p className="studio-integrity">{ui("حركة وأبعاد تفكيك توضيحية؛ القيم من المحاكي الأصلي. ")}{ui(engine?'الدورة 720°؛ الحركة مبطّأة.':turbo?'حركة الدوّار مبطّأة؛ سرعة التيربو غير محسوبة.':'مسارات التدفق تعليمية.')}{ui(reduced?' الحركة التلقائية متوقفة حسب تفضيل جهازك.':'')}</p>
      </div>
    </>:<><div className="model-controls">{!engine&&<button onClick={()=>setBody(!body)} disabled={p.layer!=='vehicle'}>{ui(p.layer!=='vehicle'?'الأجزاء مكشوفة':body?'أظهر الهيكل':'اكشف الأجزاء')}</button>}<button aria-label={ui("تكبير النموذج")} onClick={()=>setZoomRequest(z=>({seq:z.seq+1,factor:1.22}))}>＋</button><button aria-label={ui("تصغير النموذج")} onClick={()=>setZoomRequest(z=>({seq:z.seq+1,factor:1/1.22}))}>−</button><button onClick={()=>setReset(r=>r+1)}>{ui("إعادة المنظور")}</button>{p.layer!=='vehicle'&&!engine&&<button onClick={()=>setDemo(!demo)}>{ui(demo?'أوقف حركة المسار':'حرّك المسار')}</button>}</div><p className="model-hint">{ui(engine?uiTemplate("المحرك مكبّر للتعلّم · {0}", "Engine enlarged for learning · {0}", p.stroke==null?'حركة الأشواط مبطّأة':['السحب: يدخل الهواء والوقود','الضغط: يصعد المكبس','القدرة: يدفع الاحتراق المكبس','العادم: تخرج الغازات'][p.stroke]):'اسحب لتدوير السيارة · اضغط الجزء لتفهمه')}{demo&&<small>{ui("حركة توضيحية؛ لا تغيّر المحاكاة")}</small>}</p></>}
  </section>;
}





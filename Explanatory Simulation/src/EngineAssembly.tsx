import { useUI } from './useUI';
import { createContext, useContext, useEffect, useMemo, useRef, type ReactNode } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { SceneClock } from './SceneClock';
import { cylinderPose } from './model/layout.mjs';
import { beveledBox } from './model/casting.mjs';
import { CYLINDER_COUNT, cylinderX, headPortAnchors, fuelRouteAnchors, fuelFlowAvailable, VALVE_GEOMETRY, FUEL_GEOMETRY, GAS_GEOMETRY, gasFlowCurve, gasFlowAvailable, type EnginePoint } from './model/engine-ports.mjs';
import { strokeAtDegrees, sparkPulseAtDegrees, combustionAtDegrees } from './model/engine-cycle.mjs';

type Appearance = 'solid' | 'ghost' | 'section';
type Concept = 't_block' | 'engine' | 'four_stroke' | 'engine_torque' | 'spark' | 't_oil' | 'air' | 'egt' | 'fuel';
type PartId = 'head' | 'block' | 'piston' | 'crank' | 'spark' | 'pan' | 'intake' | 'exhaust' | 'injector';

export type EngineAssemblyProps = {
  frame: any;
  onSelect: (id: string) => void;
  onPartSelect?: (part: string) => void;
  onCylinderSelect?: (index: number) => void;
  selectedPart?: string;
  selectedCylinder?: number;
  isolatedPart?: string | null;
  explode: number;
  appearance: Appearance;
  study?: boolean;
  crossSection?: boolean;
};

const BASE = { x: 1.49, y: 0.72, z: -0.06 } as const;
const CYLINDER_X = cylinderX;
const Y_AXIS = new THREE.Vector3(0, 1, 0);
const CylinderMuted = createContext(false);
const COLORS = {
  casting: '#45524f', castingEdge: '#66716d', blockFace: '#596864',
  steel: '#b4bfbb', machined: '#d0d6d1', piston: '#c7d0cc',
  brass: '#b88b55', copper: '#b76f4b', dark: '#273735', gasket: '#252c2b',
  air: '#3b9daf', exhaust: '#d07a51', oil: '#b78b50', fuel: '#df78dc', highlight: '#f0ae53',
};
function thermalColor(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return COLORS.steel;
  const hue = 0.56 - THREE.MathUtils.clamp((value - 290) / 650, 0, 0.5);
  return `#${new THREE.Color().setHSL(hue, 0.48, 0.5).getHexString()}`;
}

function inspectPart(props: EngineAssemblyProps, id: PartId, concept: Concept, cylinderIndex?: number) {
  if (cylinderIndex !== undefined) props.onCylinderSelect?.(cylinderIndex);
  props.onPartSelect?.(id);
  props.onSelect(concept);
}

function Material({
  appearance, color, selected = false, metalness = 0.72, roughness = 0.34,
  inside = false,
}: {
  appearance: Appearance; color: string; selected?: boolean;
  metalness?: number; roughness?: number; inside?: boolean;
}) {
  const muted = useContext(CylinderMuted);
  const translucent = appearance === 'ghost' || (inside && appearance === 'section');
  const opacity = muted ? 0.16 : appearance === 'ghost' ? (inside ? 0.22 : 0.3) : translucent ? 0.26 : 1;
  return <meshPhysicalMaterial
    color={color} metalness={metalness} roughness={roughness} clearcoat={0.18}
    transparent={translucent || muted} opacity={opacity} depthWrite={!translucent && !muted}
    side={THREE.DoubleSide}
    emissive={selected ? COLORS.highlight : '#000000'}
    emissiveIntensity={selected ? 0.34 : 0}
  />;
}

function Part({
  id, concept, props, visible = true, cylinderIndex, children,
}: {
  id: PartId; concept: Concept; props: EngineAssemblyProps;
  visible?: boolean; cylinderIndex?: number; children: ReactNode;
}) {
  const { ui } = useUI();

  const { isolatedPart } = props;
  const { gl } = useThree();
  return <group
    name={`engine-part-${id}${cylinderIndex === undefined ? '' : `-${cylinderIndex + 1}`}`}
    userData={{ part: id, concept, cylinderIndex }}
    visible={visible && (!isolatedPart || isolatedPart === id)}
    onPointerOver={() => { gl.domElement.style.cursor = 'pointer'; }}
    onPointerOut={() => { gl.domElement.style.cursor = ''; }}
    onClick={(event: { stopPropagation: () => void }) => {
      event.stopPropagation();
      inspectPart(props, id, concept, cylinderIndex);
    }}
  >{ui(children)}</group>;
}

function HeadPassage({ points, color, appearance, selected }: {points: EnginePoint[]; color: string; appearance: Appearance; selected: boolean}) {
  const muted = useContext(CylinderMuted);
  const geometry = useMemo(() => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p))), 24, 0.012, 8, false), [points]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <mesh geometry={geometry}>
    <meshStandardMaterial color={color} emissive={selected ? color : '#000000'} emissiveIntensity={selected ? 0.5 : 0.08}
      transparent opacity={muted ? 0.12 : appearance === 'solid' ? 0.7 : 0.35} depthWrite={false}/>
  </mesh>;
}

/** Arrows and packets follow the same cylinder phase as its valves and piston. */
function PortFlow({ points, color, side, index, connected, showArrows }: {
  points: EnginePoint[]; color: string; side: 'intake' | 'exhaust'; index: number; connected: boolean; showArrows: boolean;
}) {
  const { ui } = useUI();

  const clock = useContext(SceneClock);
  const muted = useContext(CylinderMuted);
  const group = useRef<THREE.Group>(null);
  const packets = useRef<(THREE.Mesh | null)[]>([]);
  const curve = useMemo(() => gasFlowCurve(points), [points]);
  const arrows = useMemo(() => GAS_GEOMETRY.arrowStations.map(t => ({
    position: curve.getPoint(t), rotation: new THREE.Quaternion().setFromUnitVectors(Y_AXIS, curve.getTangent(t).normalize()),
  })), [curve]);
  useFrame(() => {
    const degrees = ((clock.cycle + index / CYLINDER_COUNT) % 1) * 720;
    if (group.current) group.current.visible = gasFlowAvailable(degrees, side, connected, muted);
    packets.current.forEach((mesh, i) => mesh?.position.copy(curve.getPoint((clock.time * 0.7 + degrees / 720 + i / 3) % 1)));
  });
  return <group ref={group} visible={false}>
    {Array.from({length: 3}, (_, i) => <mesh key={i} ref={mesh => { packets.current[i] = mesh; }}>
      <sphereGeometry args={[GAS_GEOMETRY.packetRadius, 10, 8]}/><meshBasicMaterial color={color} depthWrite={false}/>
    </mesh>)}
    {showArrows && arrows.map((arrow, i) => <mesh key={i} position={arrow.position} quaternion={arrow.rotation}>
      <coneGeometry args={[GAS_GEOMETRY.arrowRadius, GAS_GEOMETRY.arrowHeight, 10]}/><meshBasicMaterial color={color} depthWrite={false}/>
    </mesh>)}
  </group>;
}

/** Polyline with the physical nozzle and port endpoints; no curve overshoot. */
function FuelFlow({ route, index, frame, showArrows }: { route: ReturnType<typeof fuelRouteAnchors>; index: number; frame: any; showArrows: boolean }) {
  const { ui } = useUI();

  const clock = useContext(SceneClock), muted = useContext(CylinderMuted);
  const group = useRef<THREE.Group>(null), packets = useRef<(THREE.Mesh | null)[]>([]);
  const { curve, geometry, arrows } = useMemo(() => {
    const curve = new THREE.CurvePath<THREE.Vector3>();
    route.flow.slice(1).forEach((p, i) => curve.add(new THREE.LineCurve3(new THREE.Vector3(...route.flow[i]), new THREE.Vector3(...p))));
    return { curve, geometry: new THREE.TubeGeometry(curve, 64, FUEL_GEOMETRY.tubeRadius, 6, false), arrows: FUEL_GEOMETRY.arrowStations.map(t => ({ position: curve.getPoint(t), rotation: new THREE.Quaternion().setFromUnitVectors(Y_AXIS, curve.getTangent(t).normalize()) })) };
  }, [route]);
  const sample = useMemo(() => new THREE.Vector3(), []);
  useEffect(() => () => geometry.dispose(), [geometry]);
  useFrame(() => {
    const degrees = ((clock.cycle + index / CYLINDER_COUNT) % 1) * 720;
    if (group.current) group.current.visible = !muted && fuelFlowAvailable(degrees, frame?.lam, route.connected);
    for (let i = 0; i < packets.current.length; i++) {
      const mesh = packets.current[i];
      if (mesh) mesh.position.copy(curve.getPoint((clock.time * .7 + degrees / 720 + i / 3) % 1, sample));
    }
  });
  return <group ref={group} visible={false}>
    <mesh geometry={geometry}><meshBasicMaterial color={COLORS.fuel} transparent opacity={.65} depthWrite={false}/></mesh>
    {[0,1,2].map(i => <mesh key={i} ref={mesh => { packets.current[i] = mesh; }}><sphereGeometry args={[FUEL_GEOMETRY.packetRadius,8,6]}/><meshBasicMaterial color={COLORS.fuel}/></mesh>)}
    {showArrows && arrows.map((a,i) => <mesh key={i} position={a.position} quaternion={a.rotation}><coneGeometry args={[FUEL_GEOMETRY.arrowRadius,FUEL_GEOMETRY.arrowHeight,8]}/><meshBasicMaterial color={COLORS.fuel}/></mesh>)}
  </group>;
}

function Valve({ anchor, valveRef, color, appearance, selected }: {
  anchor: EnginePoint; valveRef: React.RefObject<THREE.Group | null>; color: string; appearance: Appearance; selected: boolean;
}) {
  return <>
    <mesh position={anchor} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[0.019, 0.003, 8, 20]}/><Material appearance={appearance} color={color} selected={selected}/>
    </mesh>
    <group ref={valveRef} position={anchor}>
      <mesh><cylinderGeometry args={[VALVE_GEOMETRY.discRadius, VALVE_GEOMETRY.discRadius, VALVE_GEOMETRY.discHeight, 20]}/><Material appearance={appearance} color={color} selected={selected}/></mesh>
      <mesh position={[0, VALVE_GEOMETRY.stemOffset, 0]}><cylinderGeometry args={[VALVE_GEOMETRY.stemRadius, VALVE_GEOMETRY.stemRadius, VALVE_GEOMETRY.stemHeight, 10]}/><Material appearance={appearance} color={COLORS.machined} selected={selected}/></mesh>
    </group>
  </>;
}

function CylinderUnit({ index, props, explode }: { index: number; props: EngineAssemblyProps; explode: number }) {
  const { ui, uiTemplate } = useUI();

  const clock = useContext(SceneClock);
  const piston = useRef<THREE.Group>(null);
  const rod = useRef<THREE.Mesh>(null);
  const throwGroup = useRef<THREE.Group>(null);
  const intakeValve = useRef<THREE.Group>(null);
  const exhaustValve = useRef<THREE.Group>(null);
  const movementArrow = useRef<THREE.Group>(null);
  const chamber = useRef<THREE.Mesh>(null);
  const flame = useRef<THREE.Mesh>(null);
  const sparkFlash = useRef<THREE.Mesh>(null);
  const direction = useMemo(() => new THREE.Vector3(), []);
  const pin = useMemo(() => new THREE.Vector3(), []);
  const joint = useMemo(() => new THREE.Vector3(), []);
  const angleOffset = index / 6;
  const phase = (clock.cycle + angleOffset) % 1;
  const pose = cylinderPose(phase);
  const selected = props.selectedPart === 'block';
  const chosen = props.selectedCylinder === index;
  const muted = !!props.study && !chosen;
  const pistonSelected = props.selectedPart === 'piston' && chosen;
  const crankSelected = props.selectedPart === 'crank';
  const separation = Math.max(0, Math.min(1, props.explode));
  const ports = useMemo(() => headPortAnchors(index, separation), [index, separation]);
  const fuelRoute = useMemo(() => fuelRouteAnchors(index, separation), [index, separation]);

  useFrame(() => {
    const cycle = (clock.cycle + angleOffset) % 1;
    const stroke = strokeAtDegrees(cycle * 720);
    const current = cylinderPose(cycle);
    pin.set(CYLINDER_X(index), current.pinY, -0.06 + current.pinZ);
    joint.set(CYLINDER_X(index), current.jointY, -0.06);
    if (piston.current) piston.current.position.y = current.pistonY;
    if (rod.current) {
      rod.current.position.copy(pin).add(joint).multiplyScalar(0.5);
      direction.copy(joint).sub(pin);
      rod.current.scale.y = direction.length();
      rod.current.quaternion.setFromUnitVectors(Y_AXIS, direction.normalize());
    }
    if (throwGroup.current) throwGroup.current.rotation.x = cycle * Math.PI * 4;
    if (intakeValve.current) intakeValve.current.position.y = ports.intake.valve[1] - (stroke.intakeOpen ? VALVE_GEOMETRY.lift : 0);
    if (exhaustValve.current) exhaustValve.current.position.y = ports.exhaust.valve[1] - (stroke.exhaustOpen ? VALVE_GEOMETRY.lift : 0);
    if (movementArrow.current) {
      movementArrow.current.position.y = current.pistonY;
      movementArrow.current.rotation.z = stroke.pistonDirection === 'up' ? 0 : Math.PI;
    }
    if (chamber.current) {
      const top = ports.bore.center[1] + ports.bore.height / 2;
      const bottom = current.pistonY + 0.065 / 2;
      chamber.current.position.y = (top + bottom) / 2;
      chamber.current.scale.y = Math.max(0.001, top - bottom);
      (chamber.current.material as THREE.MeshBasicMaterial).color.set(stroke.id === 'intake' || stroke.id === 'compression' ? COLORS.air : COLORS.exhaust);
    }
    const burn = combustionAtDegrees(cycle * 720, props.frame?.spark);
    const pulse = sparkPulseAtDegrees(cycle * 720, props.frame?.spark);
    if (flame.current) {
      const material = flame.current.material as THREE.MeshBasicMaterial;
      material.opacity = ports.flowConnected && !muted ? burn * 0.78 : 0;
      flame.current.scale.setScalar(0.45 + burn * 0.55);
    }
    if (sparkFlash.current) (sparkFlash.current.material as THREE.MeshBasicMaterial).opacity = ports.flowConnected && !muted ? pulse * 0.95 : 0;
  });

  return <CylinderMuted.Provider value={muted}>
    <Part id="block" concept="t_block" props={props} cylinderIndex={index}>
      <group>
        <mesh position={ports.bore.center} castShadow receiveShadow>
          {props.appearance === 'section'
            ? <cylinderGeometry args={[ports.bore.radius, ports.bore.radius, ports.bore.height, 32, 1, true, props.crossSection ? Math.PI : Math.PI / 2, Math.PI]}/>
            : <cylinderGeometry args={[ports.bore.radius, ports.bore.radius, ports.bore.height, 32, 1, true]}/>}
          <Material appearance={props.appearance} color={COLORS.steel} selected={selected} metalness={0.82} roughness={0.26}/>
        </mesh>
        <mesh position={[ports.bore.center[0], ports.bore.center[1] + ports.bore.height / 2 - 0.006, ports.bore.center[2]]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.073, 0.006, 8, 28]}/>
          <Material appearance={props.appearance} color={COLORS.machined} selected={selected} metalness={0.78} roughness={0.24}/>
        </mesh>
      </group>
    </Part>

    <Part id="piston" concept="four_stroke" props={props} cylinderIndex={index}>
      <group ref={piston} position={[CYLINDER_X(index), pose.pistonY, -0.06]}>
        {props.study && props.selectedPart==='piston' && !props.crossSection && <Html position={[0, 0.07, 0.07]} center zIndexRange={[1,0]}>
          <button className={`engine-piston-choice${chosen?' active':''}`} aria-label={ui(uiTemplate("اختيار مكبس الأسطوانة {0}", "Select cylinder {0} piston", index+1))} onClick={()=>inspectPart(props,'piston','four_stroke',index)}>{ui(index+1)}</button>
        </Html>}
        <mesh castShadow>
          <cylinderGeometry args={[0.073, 0.076, 0.065, 32]}/>
          <Material appearance="solid" color={COLORS.piston} selected={pistonSelected} metalness={0.84} roughness={0.23}/>
        </mesh>
        {[0.017, 0, -0.017].map((offset) => <mesh key={offset} position={[0, offset, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.074, 0.0042, 6, 28]}/>
          <Material appearance="solid" color={offset === 0 ? COLORS.dark : COLORS.brass} metalness={0.76} roughness={0.3}/>
        </mesh>)}
        <mesh position={[0, -0.027, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.012, 0.012, 0.13, 12]}/>
          <Material appearance="solid" color={COLORS.steel} metalness={0.85} roughness={0.24}/>
        </mesh>
      </group>
      <mesh ref={rod} position={[CYLINDER_X(index), 0.75, -0.06]}>
        <cylinderGeometry args={[0.017, 0.027, 1, 12]}/>
        <Material appearance="solid" color={COLORS.brass} selected={pistonSelected} metalness={0.78} roughness={0.26}/>
      </mesh>
    </Part>

    {props.study && chosen && <>
      <Html position={[CYLINDER_X(index), 1.265 + separation * 0.18, -0.06]} center zIndexRange={[1, 0]} style={{pointerEvents: 'none'}}>
        <span className="engine-cylinder-label">{ui("أسطوانة ")}{ui(index + 1)}</span>
      </Html>
      <group ref={movementArrow} position={[CYLINDER_X(index) + 0.105, pose.pistonY, 0.025]}>
        <mesh position={[0, 0.045, 0]}><cylinderGeometry args={[0.005, 0.005, 0.09, 8]}/><meshBasicMaterial color="#f3d091" depthTest={false}/></mesh>
        <mesh position={[0, 0.1, 0]}><coneGeometry args={[0.017, 0.034, 10]}/><meshBasicMaterial color="#f3d091" depthTest={false}/></mesh>
      </group>
      <mesh ref={chamber} position={[CYLINDER_X(index), 1.045, -0.06]} visible={props.appearance !== 'solid' && ports.flowConnected}>
        <cylinderGeometry args={[0.065, 0.065, 1, 24]}/><meshBasicMaterial color={COLORS.air} transparent opacity={0.17} depthWrite={false}/>
      </mesh>
    </>}

    <Part id="crank" concept="engine_torque" props={props}>
      <group ref={throwGroup} position={[CYLINDER_X(index), 0.59, -0.06]}>
        {[-0.067, 0.067].map((x) => <mesh key={x} position={[x, 0.0475, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.068, 0.068, 0.055, 24]}/>
          <Material appearance="solid" color={COLORS.copper} selected={crankSelected} metalness={0.82} roughness={0.28}/>
        </mesh>)}
        <mesh position={[0, 0.095, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.032, 0.032, 0.13, 20]}/>
          <Material appearance="solid" color={COLORS.machined} selected={crankSelected} metalness={0.9} roughness={0.2}/>
        </mesh>
        <mesh position={[0, 0.095, 0]} rotation={[0, Math.PI / 2, 0]}>
          <torusGeometry args={[0.024, 0.005, 8, 18]}/>
          <Material appearance="solid" color={COLORS.brass} selected={crankSelected} metalness={0.8} roughness={0.25}/>
        </mesh>
      </group>
    </Part>
    <Part id="intake" concept="air" props={props} cylinderIndex={index}>
      <HeadPassage points={ports.intake.passage} color={COLORS.air} appearance={props.appearance} selected={props.selectedPart==='intake' && props.selectedCylinder===index}/>
      <Valve anchor={ports.intake.valve} valveRef={intakeValve} color={COLORS.air} appearance={props.appearance} selected={props.selectedPart==='intake' && chosen}/>
      <PortFlow points={ports.intake.flow} color="#67dbe7" side="intake" index={index} connected={ports.flowConnected} showArrows={!!props.study && chosen}/>
    </Part>
    <Part id="exhaust" concept="egt" props={props} cylinderIndex={index}>
      <HeadPassage points={ports.exhaust.passage} color={COLORS.exhaust} appearance={props.appearance} selected={props.selectedPart==='exhaust' && props.selectedCylinder===index}/>
      <Valve anchor={ports.exhaust.valve} valveRef={exhaustValve} color={COLORS.exhaust} appearance={props.appearance} selected={props.selectedPart==='exhaust' && chosen}/>
      <PortFlow points={ports.exhaust.flow} color="#ffac70" side="exhaust" index={index} connected={ports.flowConnected} showArrows={!!props.study && chosen}/>
    </Part>
    <Part id="spark" concept="spark" props={props} cylinderIndex={index}>
      <group position={[CYLINDER_X(index), 0, -0.06]}>
        <mesh ref={flame} position={[0, 1.023, 0]}>
          <sphereGeometry args={[0.026, 14, 10]}/>
          <meshBasicMaterial color={COLORS.highlight} transparent opacity={0} depthWrite={false}/>
        </mesh>
        <mesh ref={sparkFlash} position={[0, 1.039, 0]}>
          <sphereGeometry args={[0.009, 10, 8]}/>
          <meshBasicMaterial color="#fff0bd" transparent opacity={0} depthWrite={false}/>
        </mesh>
      </group>
    </Part>
    <Part id="injector" concept="fuel" props={props} cylinderIndex={index}>
      <HeadPassage points={fuelRoute.feed} color={COLORS.fuel} appearance={props.appearance} selected={props.selectedPart==='injector' && chosen}/>
      <mesh position={fuelRoute.injectorCenter}><cylinderGeometry args={[.012,.012,fuelRoute.injectorHeight,12]}/><Material appearance="solid" color={COLORS.brass} selected={props.selectedPart==='injector' && chosen}/></mesh>
      <mesh position={fuelRoute.nozzleCenter}><cylinderGeometry args={[.006,.006,fuelRoute.nozzleHeight,10]}/><Material appearance="solid" color={COLORS.fuel}/></mesh>
      {props.study && chosen && <Html position={[fuelRoute.rail[0],fuelRoute.rail[1]+.025,fuelRoute.rail[2]]} center zIndexRange={[1,0]} style={{pointerEvents:'none'}}><span className="engine-cylinder-label" style={{color:COLORS.fuel}}>{ui("وقود")}</span></Html>}
      <FuelFlow route={fuelRoute} index={index} frame={props.frame} showArrows={!!props.study && chosen}/>
    </Part>
  </CylinderMuted.Provider>;
}

function EngineInternals({ props, explode }: { props: EngineAssemblyProps; explode: number }) {
  const { ui } = useUI();

  const clock = useContext(SceneClock);
  const intakeCam = useRef<THREE.Group>(null);
  const exhaustCam = useRef<THREE.Group>(null);
  const timingGear = useRef<THREE.Group>(null);
  const headGeometry = useMemo(() => beveledBox([1.48, 0.04, 0.58], props.appearance === 'section', 0.007), [props.appearance]);
  const coverGeometry = useMemo(() => props.appearance === 'section'
    ? null : beveledBox([1.34, 0.055, 0.43], false, 0.012), [props.appearance]);
  useEffect(() => () => { headGeometry.dispose(); coverGeometry?.dispose(); }, [headGeometry, coverGeometry]);
  const camSelected = props.selectedPart === 'head';
  useFrame(() => {
    const camAngle = clock.cycle * Math.PI * 2;
    if (intakeCam.current) intakeCam.current.rotation.x = camAngle;
    if (exhaustCam.current) exhaustCam.current.rotation.x = camAngle;
    if (timingGear.current) timingGear.current.rotation.x = -camAngle;
  });
  return <>
    <Part id="head" concept="engine" props={props}>
      <group position={[0, explode * 0.18, 0]}>
        <mesh position={[BASE.x, 1.06, BASE.z]} visible={props.appearance !== 'section'} castShadow receiveShadow>
          <primitive object={headGeometry} attach="geometry"/>
          <Material appearance={props.appearance} color={COLORS.castingEdge} selected={camSelected} metalness={0.72} roughness={0.3}/>
        </mesh>
        {coverGeometry && <mesh position={[BASE.x, 1.015, BASE.z]} castShadow>
          <primitive object={coverGeometry} attach="geometry"/>
          <Material appearance={props.appearance} color={COLORS.casting} selected={camSelected} metalness={0.65} roughness={0.38}/>
        </mesh>}
        {[-0.094, -0.026].map((z, bank) => <group key={z} ref={bank === 0 ? intakeCam : exhaustCam} position={[BASE.x, 1.14, z]}>
          <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
            <cylinderGeometry args={[0.011, 0.011, 1.25, 24]}/>
            <Material appearance={props.appearance} color={COLORS.steel} selected={camSelected} metalness={0.9} roughness={0.22}/>
          </mesh>
          {Array.from({ length: 6 }, (_, i) => <mesh key={i} visible={!props.crossSection || props.selectedCylinder===i} position={[CYLINDER_X(i) - BASE.x, 0, 0]} rotation={[0, Math.PI / 2, 0]} scale={[1, 1.45, 1]}>
            <torusGeometry args={[0.014, 0.004, 8, 16]}/>
            <Material appearance={props.appearance} color={COLORS.brass} selected={camSelected} metalness={0.78} roughness={0.28}/>
          </mesh>)}
        </group>)}
        <group ref={timingGear} position={[2.12, 1.14, BASE.z]} visible={!props.crossSection}>
          <mesh rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.074, 0.074, 0.045, 32]}/>
            <Material appearance={props.appearance} color={COLORS.brass} selected={camSelected} metalness={0.82} roughness={0.25}/>
          </mesh>
          {Array.from({ length: 12 }, (_, i) => {
            const a = i * Math.PI / 6;
            return <mesh key={i} position={[0, Math.cos(a) * 0.074, Math.sin(a) * 0.074]}>
              <boxGeometry args={[0.042, 0.019, 0.018]}/>
              <Material appearance={props.appearance} color={COLORS.machined} selected={camSelected} metalness={0.84} roughness={0.24}/>
            </mesh>;
          })}
        </group>
      </group>
    </Part>

    <Part id="injector" concept="fuel" props={props}>
      <group position={[0, explode * 0.18, 0]}>
        <mesh position={[BASE.x, 1.184, fuelRouteAnchors(0).rail[2]]} rotation={[0,0,Math.PI/2]}>
          <cylinderGeometry args={[0.012, 0.012, 1.26, 12]}/>
          <Material appearance="solid" color={COLORS.brass} selected={props.selectedPart==='injector'} metalness={0.7}/>
        </mesh>
      </group>
    </Part>

    {Array.from({ length: 6 }, (_, i) => {
      const sparkSelected = props.selectedPart === 'spark' && props.selectedCylinder === i;
      return <CylinderMuted.Provider key={i} value={!!props.study && props.selectedCylinder !== i}>
      <Part id="spark" concept="spark" props={props} cylinderIndex={i} visible={!props.crossSection || props.selectedCylinder === i}>
        <group position={[CYLINDER_X(i), explode * 0.18, BASE.z]}>
          <mesh position={[0, 1.058, 0]}>
            <cylinderGeometry args={[0.003, 0.003, 0.044, 8]}/>
            <Material appearance="solid" color={COLORS.machined} selected={sparkSelected}/>
          </mesh>
          <mesh position={[0, 1.098, 0]}>
            <cylinderGeometry args={[0.012, 0.014, 0.036, 12]}/>
            <Material appearance="solid" color={COLORS.machined} selected={sparkSelected} metalness={0.85} roughness={0.23}/>
          </mesh>
          <mesh position={[0, 1.129, 0]}>
            <cylinderGeometry args={[0.009, 0.009, 0.026, 12]}/>
            <Material appearance="solid" color="#d5dedc" roughness={0.27} metalness={0.18} selected={sparkSelected}/>
          </mesh>
          <mesh position={[0, 1.142, 0]}>
            <cylinderGeometry args={[0.013, 0.013, 0.006, 6]}/>
            <Material appearance="solid" color={COLORS.brass} selected={sparkSelected} metalness={0.8} roughness={0.26}/>
          </mesh>
        </group>
      </Part></CylinderMuted.Provider>;
    })}
  </>;
}

/**
 * Inline-six teaching assembly in the source Supra's +X-forward frame.
 * These shapes explain the model's mechanisms; they are not measured CAD.
 */
export function EngineAssembly(props: EngineAssemblyProps) {
  const { ui } = useUI();

  const separation = Math.max(0, Math.min(1, Number.isFinite(props.explode) ? props.explode : 0));
  const blockSelected = props.selectedPart === 'block';
  const crankSelected = props.selectedPart === 'crank';
  const panSelected = props.selectedPart === 'pan';
  const blockGeometry = useMemo(() => props.appearance === 'section'
    ? beveledBox([1.48, 0.36, 0.58], true, 0.026)
    : beveledBox([1.48, 0.36, 0.58], false, 0.026), [props.appearance]);
  useEffect(() => () => blockGeometry?.dispose(), [blockGeometry]);
  const panGeometry = useMemo(() => beveledBox([1.38, 0.17, 0.55], props.appearance === 'section', 0.022), [props.appearance]);
  const sumpGeometry = useMemo(() => beveledBox([1.04, 0.035, 0.39], false, 0.008), []);
  useEffect(() => () => { panGeometry.dispose(); sumpGeometry.dispose(); }, [panGeometry, sumpGeometry]);
  const blockColor = thermalColor(props.frame?.t_block);
  const oilColor = thermalColor(props.frame?.t_oil);

  return <group name="inline-six-engine-assembly">
    <Part id="block" concept="t_block" props={props} visible={!props.crossSection}>
      <group position={[0, -separation * 0.045, 0]}>
        <mesh position={[BASE.x, BASE.y, BASE.z]} castShadow receiveShadow>
          <primitive object={blockGeometry} attach="geometry"/>
          <Material appearance={props.appearance} color={blockColor} selected={blockSelected} metalness={0.72} roughness={0.42}/>
        </mesh>
        {Array.from({ length: 5 }, (_, i) => <mesh key={i} position={[1.02 + i * 0.235, 0.72, 0.223]}>
          <boxGeometry args={[0.035, 0.22, 0.018]}/>
          <Material appearance={props.appearance} color={COLORS.castingEdge} selected={blockSelected} metalness={0.66} roughness={0.4}/>
        </mesh>)}
        {Array.from({ length: 10 }, (_, i) => <mesh key={i} position={[0.86 + (i % 5) * 0.305, 0.875, i < 5 ? 0.235 : -0.355]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.013, 0.013, 0.012, 10]}/>
          <Material appearance={props.appearance} color={COLORS.machined} selected={blockSelected} metalness={0.85} roughness={0.22}/>
        </mesh>)}
      </group>
    </Part>

    {Array.from({ length: CYLINDER_COUNT }, (_, index) => (!props.crossSection || props.selectedCylinder === index) && <CylinderUnit key={index} index={index} props={props} explode={separation}/>)}

    <Part id="crank" concept="engine_torque" props={props} visible={!props.crossSection}>
      <mesh position={[1.49, 0.59, -0.06]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.035, 0.035, 1.34, 28]}/>
        <Material appearance="solid" color={COLORS.steel} selected={crankSelected} metalness={0.9} roughness={0.2}/>
      </mesh>
      {Array.from({ length: 6 }, (_, i) => <mesh key={i} position={[CYLINDER_X(i), 0.59, BASE.z]} rotation={[0, Math.PI / 2, 0]}>
        <torusGeometry args={[0.046, 0.008, 8, 20]}/>
        <Material appearance="solid" color={COLORS.dark} selected={crankSelected} metalness={0.62} roughness={0.33}/>
      </mesh>)}
    </Part>

    <Part id="pan" concept="t_oil" props={props} visible={!props.crossSection}>
      <group position={[0, -separation * 0.14, 0]}>
        <mesh position={[BASE.x, 0.5, BASE.z]} castShadow>
          <primitive object={panGeometry} attach="geometry"/>
          <Material appearance={props.appearance} color={oilColor} selected={panSelected} metalness={0.5} roughness={0.43}/>
        </mesh>
        <mesh position={[BASE.x, 0.405, BASE.z]}>
          <primitive object={sumpGeometry} attach="geometry"/>
          <Material appearance={props.appearance} color={COLORS.oil} selected={panSelected} metalness={0.74} roughness={0.33}/>
        </mesh>
        {Array.from({ length: 8 }, (_, i) => <mesh key={i} position={[0.91 + i * 0.166, 0.583, 0.198]}>
          <sphereGeometry args={[0.012, 8, 6]}/>
          <Material appearance={props.appearance} color={COLORS.machined} selected={panSelected} metalness={0.84} roughness={0.24}/>
        </mesh>)}
      </group>
    </Part>

    <EngineInternals props={props} explode={separation}/>
  </group>;
}

export default EngineAssembly;



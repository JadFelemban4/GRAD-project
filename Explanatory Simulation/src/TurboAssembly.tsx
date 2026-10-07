import { useUI } from './useUI';
import { useContext, useEffect, useMemo, useRef, type ReactNode } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { SceneClock } from './SceneClock';
import {
  TURBO_CENTER, turboAnchors, turboFlowData, turboFlowPaths,
  flowVisual, turboHousingPosition, advanceTurboPhase,
} from './model/turbo-layout.mjs';

type Appearance = 'solid' | 'ghost' | 'section';
type TurboSide = 'compressor' | 'turbine';
type Point = [number, number, number];
export type TurboAssemblyProps = {
  frame: any;
  appearance: Appearance;
  explode: number;
  selectedPart: string;
  isolatedPart: string | null;
  onPartSelect: (id: string) => void;
  onSelect: (concept: string) => void;
  flowStep: number;
};

const CYAN = '#59bdca';
const ORANGE = '#e08a58';
const STEEL = '#b9c6c2';
const DARK = '#344442';
const BRASS = '#c0985d';
const AMBER = '#f0b45f';
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

function tempColor(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return STEEL;
  const hue = 0.56 - THREE.MathUtils.clamp((value - 290) / 650, 0, 0.5);
  return `#${new THREE.Color().setHSL(hue, 0.52, 0.49).getHexString()}`;
}

function annularCover(outerRadius: number, innerRadius: number, depth: number) {
  const shape = new THREE.Shape();
  shape.absarc(0, 0, outerRadius, 0, Math.PI * 2, false);
  const opening = new THREE.Path();
  opening.absarc(0, 0, innerRadius, 0, Math.PI * 2, true);
  shape.holes.push(opening);
  const geometry = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 48 });
  geometry.translate(0, 0, -depth / 2);
  geometry.computeVertexNormals();
  return geometry;
}

function Finish({
  appearance, color, selected, active = true, metalness = 0.76, roughness = 0.3,
}: {
  appearance: Appearance; color: string; selected: boolean; active?: boolean;
  metalness?: number; roughness?: number;
}) {
  const baseOpacity = appearance === 'ghost' ? 0.28 : 1;
  const opacity = baseOpacity * (active ? 1 : 0.34);
  const transparent = opacity < 1;
  return <meshPhysicalMaterial
    color={color} metalness={metalness} roughness={roughness} clearcoat={0.2}
    transparent={transparent} opacity={opacity} depthWrite={!transparent}
    side={THREE.DoubleSide}
    emissive={selected ? AMBER : '#000000'} emissiveIntensity={selected ? 0.16 : 0}
  />;
}

function TurboPart({
  id, concept, props, active = true, position, children,
}: {
  id: string; concept: string; props: TurboAssemblyProps; active?: boolean;
  position?: Point; children: ReactNode;
}) {
  const { ui } = useUI();

  const { gl } = useThree();
  const isolateLinkedShaft = id === 'turbo-shaft' && ['compressor', 'turbine'].includes(props.isolatedPart ?? '');
  const visible = !props.isolatedPart || props.isolatedPart === id || isolateLinkedShaft;
  return <group
    name={`turbo-part-${id}`} userData={{ part: id, concept }} position={position} visible={visible}
    onPointerOver={() => { gl.domElement.style.cursor = 'pointer'; }}
    onPointerOut={() => { gl.domElement.style.cursor = ''; }}
    onClick={(event: { stopPropagation: () => void }) => {
      event.stopPropagation();
      props.onPartSelect(id);
      props.onSelect(concept);
    }}
  >{ui(children)}</group>;
}

function pathCurve(points: Point[]) {
  return new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
}

function Tube({ points, color, active, radius, appearance = 'solid' }: { points: Point[]; color: string; active: boolean; radius: number; appearance?: Appearance }) {
  const curve = useMemo(() => pathCurve(points), [points]);
  const geometry = useMemo(() => new THREE.TubeGeometry(curve, 72, radius, 12, false), [curve, radius]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  const opacity = (appearance === 'ghost' ? 0.28 : 0.85) * (active ? 1 : 0.18);
  return <mesh geometry={geometry} castShadow={false}>
    <meshStandardMaterial color={active ? color : '#74817d'} metalness={0.12} roughness={0.45} transparent={opacity < 1} opacity={opacity} depthWrite={active && appearance !== 'ghost'}/>
  </mesh>;
}

function FlowPackets({
  points, color, active, mass,
}: { points: Point[]; color: string; active: boolean; mass: number | null }) {
  const { ui } = useUI();

  const clock = useContext(SceneClock);
  const curve = useMemo(() => pathCurve(points), [points]);
  const particles = useRef<(THREE.Mesh | null)[]>([]);
  const motion = useRef({time:clock.time,angle:0});
  const display = flowVisual(mass);
  useFrame(() => {
    const elapsed=clock.time-motion.current.time;motion.current.time=clock.time;
    if (!display || mass === null || mass <= 0) return;
    motion.current.angle=advanceTurboPhase(motion.current.angle,elapsed,display.speed*0.18*Math.PI*2);
    particles.current.forEach((mesh, i) => {
      if (!mesh) return;
      mesh.position.copy(curve.getPoint((motion.current.angle / (Math.PI*2) + i / 5) % 1));
      mesh.scale.setScalar(display.density * (active ? 1 : 0.72));
    });
  });
  return <group visible={active && mass !== null && mass > 0}>
    {Array.from({ length: 5 }, (_, i) => <mesh key={i} ref={(mesh) => { particles.current[i] = mesh; }}>
      <sphereGeometry args={[0.017, 10, 8]}/>
      <meshBasicMaterial color={color}/>
    </mesh>)}
  </group>;
}

function makeBladeGeometry(depth = 0.08) {
  const shape = new THREE.Shape();
  shape.moveTo(0.055, -0.022);
  shape.quadraticCurveTo(0.14, -0.065, 0.30, 0.045);
  shape.quadraticCurveTo(0.34, 0.075, 0.315, 0.105);
  shape.quadraticCurveTo(0.18, 0.025, 0.065, 0.025);
  shape.quadraticCurveTo(0.042, 0.005, 0.055, -0.022);
  const geometry = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false, curveSegments: 5 });
  geometry.translate(0, 0, -depth / 2);
  geometry.computeVertexNormals();
  return geometry;
}

function Housing({ side, props, active }: { side: TurboSide; props: TurboAssemblyProps; active: boolean }) {
  const { ui } = useUI();

  const isCompressor = side === 'compressor';
  const center = turboHousingPosition(side, props.explode);
  const partId = isCompressor ? 'compressor-housing' : 'turbo-housing';
  const concept = isCompressor ? 'map' : 't_turb';
  const selected = props.selectedPart === partId;
  const color = isCompressor ? '#8d9a95' : tempColor(props.frame?.t_turb);
  const scrollPath = useMemo(() => isCompressor
    ? [[0.42, 0.01, 0], [0.56, 0.12, 0], [0.7, 0.31, 0], [0.93, 0.57, 0]] as Point[]
    : [[-0.93, 0.57, -0.27], [-0.74, 0.46, -0.19], [-0.56, 0.26, -0.09], [-0.42, 0.1, -0.02]] as Point[], [isCompressor]);
  const axial = useMemo(() => isCompressor
    ? [[0, 0, 0.46], [0, 0, 0.38], [0, 0, 0.1]] as Point[]
    : [[0, 0, -0.1], [0, 0, -0.3], [0, 0, -0.47]] as Point[], [isCompressor]);
  const shell = useMemo(() => {
    const start = isCompressor ? -0.35 : Math.PI - 0.35;
    const span = props.appearance === 'section' ? Math.PI * 1.55 : Math.PI * 2;
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= 96; i++) {
      const t = i / 96;
      const a = start + span * t;
      const r = 0.3 + 0.15 * t;
      points.push(new THREE.Vector3(Math.cos(a) * r, Math.sin(a) * r, 0));
    }
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points, false, 'centripetal'), 128, 0.078, 16, false);
  }, [isCompressor, props.appearance]);
  const coverGeometry = useMemo(() => annularCover(0.405, 0.15, 0.028), []);
  useEffect(() => () => { shell.dispose(); coverGeometry.dispose(); }, [shell, coverGeometry]);
  return <TurboPart id={partId} concept={concept} props={props} active={active} position={center}>
    <mesh geometry={shell} castShadow receiveShadow>
      <meshPhysicalMaterial
        color={active ? color : '#65716e'} metalness={0.76} roughness={0.32} clearcoat={0.15}
        transparent={props.appearance === 'ghost' || !active}
        opacity={(props.appearance === 'ghost' ? 0.28 : 1) * (active ? 1 : 0.34)}
        depthWrite={active && props.appearance !== 'ghost'}
        emissive={selected ? AMBER : '#000000'} emissiveIntensity={selected ? 0.16 : 0}
      />
    </mesh>
    <Tube points={scrollPath} color={color} active={active} radius={0.082} appearance={props.appearance}/>
    <Tube points={axial} color={color} active={active} radius={0.07} appearance={props.appearance}/>
    {props.appearance !== 'section' && <mesh position={[0, 0, 0.12]} castShadow>
      <primitive object={coverGeometry} attach="geometry"/>
      <Finish appearance={props.appearance} color={color} selected={selected} active={active}/>
    </mesh>}
    <mesh position={[0, 0, 0.15]}>
      <torusGeometry args={[0.442, 0.027, 10, 48]}/>
      <Finish appearance={props.appearance} color={DARK} selected={selected} active={active}/>
    </mesh>
    {Array.from({ length: 10 }, (_, i) => {
      const a = i * Math.PI / 5;
      return <mesh key={i} position={[Math.cos(a) * 0.443, Math.sin(a) * 0.443, 0.15]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.018, 0.018, 0.016, 12]}/>
        <meshStandardMaterial
          color={selected ? AMBER : '#d1d7d2'} metalness={0.82} roughness={0.24}
          transparent={props.appearance === 'ghost' || !active}
          opacity={(props.appearance === 'ghost' ? 0.42 : 1) * (active ? 1 : 0.38)}
          depthWrite={active && props.appearance !== 'ghost'}
        />
      </mesh>;
    })}
  </TurboPart>;
}

function Rotor({ side, props, active, phase }: { side: TurboSide; props: TurboAssemblyProps; active: boolean; phase: {current:{angle:number}} }) {
  const { ui } = useUI();

  const rotor = useRef<THREE.Group>(null);
  const blade = useMemo(() => makeBladeGeometry(), []);
  const selected = props.selectedPart === side;
  const z = side === 'compressor' ? 0.44 : -0.44;
  useEffect(() => () => blade.dispose(), [blade]);
  useFrame(() => {
    if (!rotor.current) return;
    rotor.current.rotation.z = phase.current.angle;
  });
  return <TurboPart id={side} concept={side === 'compressor' ? 'map' : 'egt'} props={props} active={active} position={[0, 0.85, z]}>
    <group ref={rotor}>
      <mesh position={[0, 0, 0.012]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.275, 0.29, 0.024, 48]}/>
        <Finish appearance="solid" color={side === 'compressor' ? '#95a6a1' : '#a17458'} selected={selected} active={active} metalness={0.82} roughness={0.26}/>
      </mesh>
      {Array.from({ length: side === 'compressor' ? 9 : 11 }, (_, i) => <mesh key={i} geometry={blade} position={[0, 0, 0.065]} rotation={[0, 0, i * Math.PI * 2 / (side === 'compressor' ? 9 : 11)]} castShadow>
        <Finish appearance="solid" color={side === 'compressor' ? STEEL : '#cc9169'} selected={selected} active={active} metalness={0.88} roughness={0.21}/>
      </mesh>)}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.075, 0.075, 0.09, 28]}/>
        <Finish appearance="solid" color={BRASS} selected={selected} active={active} metalness={0.86} roughness={0.2}/>
      </mesh>
    </group>
  </TurboPart>;
}

function FlowLine({
  points, color, active, mass,
}: { points: Point[]; color: string; active: boolean; mass: number | null }) {
  return <>
    <Tube points={points} color={color} active={active} radius={0.013}/>
    <FlowPackets points={points} color={color} active={active} mass={mass}/>
  </>;
}

/** Two-spool-looking, single-shaft turbo illustration with distinct gas paths. */
export function TurboAssembly(props: TurboAssemblyProps) {
  const { ui } = useUI();

  const flows = turboFlowData(props.frame);
  const rates = [flows.air, flows.exhaust].filter((v): v is number => v !== null);
  const shaftFlow = rates.length ? Math.max(...rates) : null;
  const clock=useContext(SceneClock);
  const phase=useRef({time:clock.time,angle:0});
  useFrame(()=>{
    const elapsed=clock.time-phase.current.time;phase.current.time=clock.time;
    const display=flowVisual(shaftFlow);
    const rate=shaftFlow!==null&&shaftFlow>0&&display?1.1+display.speed*2.6:0;
    phase.current.angle=advanceTurboPhase(phase.current.angle,elapsed,rate);
  });
  const amount = clamp(Number.isFinite(props.explode) ? props.explode : 0, 0, 1);
  const step = Number.isInteger(props.flowStep) ? props.flowStep : -1;
  const activeAt = (...steps: number[]) => step < 0 || steps.includes(step);
  const shaftActive = activeAt(2);
  const compressorActive = activeAt(0, 1);
  const turbineActive = activeAt(3);
  const exhaustActive = activeAt(4);

  const housingCenters = useMemo(() => ({
    compressor: turboHousingPosition('compressor', amount),
    turbine: turboHousingPosition('turbine', amount),
  }), [amount]);
  const shiftedPaths = useMemo(() => {
    const compressorOffset = housingCenters.compressor[2] - turboAnchors.compressor[2];
    const turbineOffset = housingCenters.turbine[2] - turboAnchors.turbine[2];
    const shift = (points: Point[], z: number) => points.map(([x, y, pz]) => [x, y, pz + z] as Point);
    return {
      airInlet: shift(turboFlowPaths.airInlet, compressorOffset),
      airCharge: shift(turboFlowPaths.airCharge, compressorOffset),
      exhaustInlet: shift(turboFlowPaths.exhaustInlet, turbineOffset),
      exhaustOutlet: shift(turboFlowPaths.exhaustOutlet, turbineOffset),
    };
  }, [housingCenters]);

  return <group name="turbocharger-assembly" userData={{ center: TURBO_CENTER }}>
    <TurboPart id="turbo-shaft" concept="turbocharger" props={props} active={shaftActive} position={turboAnchors['turbo-shaft']}>
      <mesh rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.035, 0.035, 0.88, 28]}/>
        <Finish appearance="solid" color={STEEL} selected={props.selectedPart === 'turbo-shaft'} active={shaftActive} metalness={0.91} roughness={0.2}/>
      </mesh>
      {[-0.17, 0.17].map((z) => <group key={z} position={[0, 0, z]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.105, 0.105, 0.1, 32]}/>
          <Finish appearance="solid" color={DARK} selected={props.selectedPart === 'turbo-shaft'} active={shaftActive}/>
        </mesh>
        <mesh>
          <torusGeometry args={[0.105, 0.013, 9, 32]}/>
          <Finish appearance="solid" color={BRASS} selected={props.selectedPart === 'turbo-shaft'} active={shaftActive}/>
        </mesh>
      </group>)}
    </TurboPart>

    <Rotor side="compressor" props={props} active={compressorActive} phase={phase}/>
    <Rotor side="turbine" props={props} active={turbineActive} phase={phase}/>
    <Housing side="compressor" props={props} active={compressorActive}/>
    <Housing side="turbine" props={props} active={turbineActive}/>

    <FlowLine points={shiftedPaths.airInlet} color={CYAN} active={activeAt(0)} mass={flows.air}/>
    <FlowLine points={shiftedPaths.airCharge} color={CYAN} active={activeAt(1)} mass={flows.air}/>
    <FlowLine points={shiftedPaths.exhaustInlet} color={ORANGE} active={activeAt(3)} mass={flows.exhaust}/>
    <FlowLine points={shiftedPaths.exhaustOutlet} color={ORANGE} active={exhaustActive} mass={flows.exhaust}/>
  </group>;
}

export default TurboAssembly;

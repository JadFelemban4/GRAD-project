import { useUI } from './useUI';
import { useContext, useEffect, useMemo, useRef } from 'react';
import { Html, Line } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { TurboAssembly } from './TurboAssembly';
import { SceneClock } from './SceneClock';
import { advanceTurboPhase, flowVisual, turboFlowData } from './model/turbo-layout.mjs';
import {
  vehicleAirflowPaths, vehicleTurboAnchors, VEHICLE_TURBO_MOUNT,
  type VehiclePoint,
} from './model/vehicle-airflow.mjs';

const CYAN = '#60d6e7';
const AMBER = '#f1a16c';
type Stream = 'air' | 'exhaust';

function curve(points: VehiclePoint[]) {
  return new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
}

function Pipe({ points, color, radius, opacity = 0.9, onSelect }: {
  points: VehiclePoint[]; color: string; radius: number; opacity?: number; onSelect?: () => void;
}) {
  const path = useMemo(() => curve(points), [points]);
  const geometry = useMemo(() => new THREE.TubeGeometry(path, 56, radius, 10, false), [path, radius]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <mesh geometry={geometry} onClick={onSelect ? (event) => { event.stopPropagation(); onSelect(); } : undefined}>
    <meshStandardMaterial color={color} metalness={0.3} roughness={0.32} transparent={opacity < 1} opacity={opacity} depthWrite={opacity === 1} />
  </mesh>;
}

function FlowPackets({ points, rate, color, stream }: { points: VehiclePoint[]; rate: number | null; color: string; stream: Stream }) {
  const { ui } = useUI();

  const clock = useContext(SceneClock);
  const refs = useRef<Array<THREE.Mesh | null>>([]);
  const motion = useRef({ time: clock.time, phase: 0 });
  const path = useMemo(() => curve(points), [points]);
  const visual = flowVisual(rate);
  const count = rate !== null && rate > 0 && visual ? Math.min(6, Math.max(2, Math.ceil(visual.density * 3))) : 0;
  useFrame(() => {
    const valid = visual && rate !== null && rate > 0;
    motion.current.phase = advanceTurboPhase(motion.current.phase, clock.time - motion.current.time, valid ? visual.speed * (stream === 'exhaust' ? 0.83 : 1) * Math.PI * 2 : 0);
    motion.current.time = clock.time;
    refs.current.forEach((mesh, i) => {
      if (!mesh) return;
      if (!valid) { mesh.visible = false; return; }
      mesh.visible = i < count;
      const travel = (motion.current.phase / (Math.PI * 2) + i / 6) % 1;
      mesh.position.copy(path.getPointAt(travel));
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), path.getTangentAt(travel));
    });
  });
  return <group>
    {Array.from({ length: 6 }, (_, i) => <mesh key={i} ref={(node) => { refs.current[i] = node; }} visible={false}>
      <coneGeometry args={[0.045, 0.14, 8]} />
      <meshBasicMaterial color={color} toneMapped={false} />
    </mesh>)}
  </group>;
}

function Part({ position, size, color, onClick }: { position: VehiclePoint; size: VehiclePoint; color: string; onClick: () => void }) {
  return <mesh position={position} onClick={(event) => { event.stopPropagation(); onClick(); }} castShadow>
    <boxGeometry args={size} />
    <meshStandardMaterial color={color} metalness={0.55} roughness={0.35} />
  </mesh>;
}

function Callout({ position, target, text, color, onClick }: {
  position: VehiclePoint; target: VehiclePoint; text: string; color: string; onClick?: () => void;
}) {
  const { ui } = useUI();

  const { gl } = useThree();
  const portal = useMemo(() => ({ current: gl.domElement.parentElement! }), [gl]);
  return <>
    <Line points={[position, target]} color={color} transparent opacity={0.75} lineWidth={1.35} />
    <Html portal={portal} position={position} center zIndexRange={[3,0]} style={{ left:0, pointerEvents: onClick ? 'auto' : 'none' }}>
      {onClick ? <button type="button" onPointerDown={(event) => event.stopPropagation()} onClick={(event) => { event.stopPropagation(); onClick(); }}
        style={labelStyle(color)}>{ui(text)}</button> : <span style={labelStyle(color)}>{ui(text)}</span>}
    </Html>
  </>;
}

const labelStyle = (color: string): React.CSSProperties => ({
  display: 'block', whiteSpace: 'nowrap', padding: '5px 9px', border: `1px solid ${color}88`,
  borderRadius: 4, background: 'rgba(8,14,21,.9)', color, font: '600 11px/1.2 "DM Sans", sans-serif',
  boxShadow: '0 2px 10px #0007', cursor: 'pointer',
});

export type VehicleAirflowProps = {
  frame: any;
  onSelect: (concept: string) => void;
  onInspectTurbo: () => void;
  onInspectCylinder?: () => void;
  active: boolean;
  showLabels?: boolean;
};

/** Car-space cooling and exhaust routes around the same reusable enlarged turbo assembly. */
export function VehicleAirflow({ frame, onSelect, onInspectTurbo, onInspectCylinder, active, showLabels=true }: VehicleAirflowProps) {
  const { ui } = useUI();

  const { size } = useThree();
  const { air, exhaust } = turboFlowData(frame);
  const choose = (concept: string) => () => onSelect(concept);
  const airPaths = [vehicleAirflowPaths.airOutside, vehicleAirflowPaths.filterToCompressor, vehicleAirflowPaths.compressorToCooler, vehicleAirflowPaths.coolerToIntake];

  return <group visible={active}>
    {/* Air cleaner and charge cooler belong to the car model; tubes are deliberately schematic. */}
    <Part position={[2.76, 0.84, 0.40]} size={[0.34, 0.20, 0.31]} color="#44515c" onClick={choose('air')} />
    <Part position={[2.56, 0.82, 0]} size={[0.15, 0.31, 0.94]} color="#6b7c82" onClick={choose('map')} />
    {Array.from({ length: 8 }, (_, i) => <mesh key={`fin-${i}`} position={[2.478, 0.69 + i * 0.037, 0]}>
      <boxGeometry args={[0.012, 0.009, 0.82]} /><meshStandardMaterial color="#a1b4b6" metalness={0.75} roughness={0.28} />
    </mesh>)}
    <Part position={[1.50, 1.06, -0.45]} size={[1.20, 0.11, 0.12]} color="#46545b" onClick={onInspectCylinder || choose('air')} />

    {airPaths.map((path, i) => i===0?<Line key={`air-pipe-${i}`} points={path} color={CYAN} lineWidth={2} dashed/>:<Pipe key={`air-pipe-${i}`} points={path} color={CYAN} radius={0.033} onSelect={choose(i === 3 ? 'map' : 'air')} />)}
    {[vehicleAirflowPaths.intakePlenumLeft, vehicleAirflowPaths.intakePlenumRight].map((path,i)=><Pipe key={`intake-rail-${i}`} points={path} color={CYAN} radius={0.023} onSelect={onInspectCylinder || choose('air')}/>)}
    {vehicleAirflowPaths.intakeBranches.map((path,i)=><Pipe key={`intake-port-${i}`} points={path} color={CYAN} radius={0.016} onSelect={onInspectCylinder || choose('air')}/>)}
    {vehicleAirflowPaths.exhaustRunners.map((path, i) => <Pipe key={`runner-${i}`} points={path} color={AMBER} radius={0.022} onSelect={choose('egt')} />)}
    {[vehicleAirflowPaths.exhaustManifoldToTurbine, vehicleAirflowPaths.turbineToTailpipe, vehicleAirflowPaths.exhaustOutside].map((path, i) =>
      i===2?<Line key={`exhaust-pipe-${i}`} points={path} color={AMBER} lineWidth={2} dashed/>:<Pipe key={`exhaust-pipe-${i}`} points={path} color={AMBER} radius={0.035} onSelect={choose('egt')} />)}
    {airPaths.map((path, i) => <FlowPackets key={`air-dots-${i}`} points={path} rate={air} color={CYAN} stream="air" />)}
    {[vehicleAirflowPaths.intakePlenumLeft, vehicleAirflowPaths.intakePlenumRight].map((path,i)=><FlowPackets key={`intake-rail-dots-${i}`} points={path} rate={air===null?null:air/2} color={CYAN} stream="air"/>)}
    {vehicleAirflowPaths.intakeBranches.map((path,i)=><FlowPackets key={`intake-branch-dots-${i}`} points={path} rate={air===null?null:air/6} color={CYAN} stream="air"/>)}
    {/* Equal branch shares illustrate six cylinders; only total flow is modelled. */}
    {vehicleAirflowPaths.exhaustRunners.map((path, i) => <FlowPackets key={`exhaust-run-dots-${i}`} points={path} rate={exhaust===null?null:exhaust/6} color={AMBER} stream="exhaust" />)}
    {[vehicleAirflowPaths.exhaustManifoldToTurbine, vehicleAirflowPaths.turbineToTailpipe, vehicleAirflowPaths.exhaustOutside].map((path, i) =>
      <FlowPackets key={`exhaust-dots-${i}`} points={path} rate={exhaust} color={AMBER} stream="exhaust" />)}

    <group position={VEHICLE_TURBO_MOUNT.position} scale={VEHICLE_TURBO_MOUNT.scale}>
      <TurboAssembly frame={frame} appearance="section" explode={0} selectedPart="overview" isolatedPart={null} onPartSelect={() => {}} onSelect={onSelect} flowStep={-1} />
    </group>

    {showLabels&&<>
    <Callout position={size.width<700?[3.65,1.15,-.2]:[3.47,1.62,1.48]} target={[3.28, 0.84, 0.38]} text={ui("هواء خارجي")} color={CYAN} onClick={choose('air')} />
    <Callout position={[2.30, 1.72, 1.55]} target={vehicleTurboAnchors.compressor} text={ui("التيربو")} color={CYAN} onClick={onInspectTurbo} />
    <Callout position={[1.16, 1.60, -1.55]} target={[1.50, 1.06, -0.45]} text={ui("هواء إلى الأسطوانات")} color={CYAN} onClick={onInspectCylinder || choose('air')} />
    <Callout position={[-3.38, 1.48, 1.52]} target={[-3.12, 0.57, 0.70]} text={ui("خروج العادم")} color={AMBER} onClick={choose('exhaust_flow')} />
    </>}
  </group>;
}

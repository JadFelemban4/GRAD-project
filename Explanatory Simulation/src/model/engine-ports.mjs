import * as THREE from 'three';
/** Shared teaching anchors in Supra coordinates (+X forward). Not OEM port CAD. */
export const CYLINDER_COUNT = 6;
export const cylinderX = index => 0.97 + index * 0.21;
export const CYLINDER_BORE = Object.freeze({ z: -0.06, y: 0.89, radius: 0.078, height: 0.36 });
export const VALVE_GEOMETRY = Object.freeze({ discRadius: .018, discHeight: .006, stemRadius: .004, stemHeight: .065, stemOffset: .034, lift: .015 });
export const FUEL_GEOMETRY = Object.freeze({ tubeRadius: .003, packetRadius: .004, arrowRadius: .007, arrowHeight: .016, arrowStations: Object.freeze([.18, .58, .93]) });
export const GAS_GEOMETRY = Object.freeze({ packetRadius: .004, arrowRadius: .008, arrowHeight: .018, arrowStations: Object.freeze([.25, .58, .89]) });
/** Straight segments preserve the measured detour without spline overshoot. */
export function gasFlowCurve(points) {
  const curve = new THREE.CurvePath();
  points.slice(1).forEach((p, i) => curve.add(new THREE.LineCurve3(new THREE.Vector3(...points[i]), new THREE.Vector3(...p))));
  return curve;
}
export function gasFlowAvailable(degrees, side, connected = true, muted = false) {
  const a = ((degrees % 720) + 720) % 720;
  return connected && !muted && Number.isFinite(degrees) && (side === 'intake' ? a < 180 : a >= 540);
}

export function headPortAnchors(index, explode = 0) {
  const x = cylinderX(index);
  const separation = Math.max(0, Math.min(1, explode));
  const headLift = separation * 0.18;
  const y = 1.018 + headLift;
  const intakeHead = [x, y, -0.355];
  const intakeValve = [x, 1.047 + headLift, CYLINDER_BORE.z - 0.034];
  const exhaustValve = [x, 1.047 + headLift, CYLINDER_BORE.z + 0.034];
  const exhaustHead = [x, y, 0.235];
  // The charge goes around the open disc, rather than through its solid centre.
  const intakeChamber = [x + 0.04, 1.027 + separation * 0.12, intakeValve[2]];
  const exhaustChamber = [x - 0.04, 1.027 + separation * 0.12, exhaustValve[2]];
  const intakePassage = [intakeHead, [x, 1.079 + headLift, -0.245], [x, 1.081 + headLift, -0.145], intakeValve];
  const exhaustPassage = [exhaustValve, [x, 1.081 + headLift, 0.025], [x, 1.079 + headLift, 0.125], exhaustHead];
  const intakeDetour = [[x + .04, 1.07 + headLift, intakeValve[2]], [x + .04, 1.044 + headLift, intakeValve[2]]];
  const exhaustDetour = [[x - .04, 1.044 + headLift, exhaustValve[2]], [x - .04, 1.07 + headLift, exhaustValve[2]]];
  return {
    bore: { center: [x, CYLINDER_BORE.y + separation * 0.12, CYLINDER_BORE.z], radius: CYLINDER_BORE.radius, height: CYLINDER_BORE.height },
    flowConnected: separation === 0,
    intake: { head: intakeHead, valve: intakeValve, chamber: intakeChamber, passage: intakePassage, flow: [...intakePassage.slice(0, -1), ...intakeDetour, intakeChamber] },
    exhaust: { head: exhaustHead, valve: exhaustValve, chamber: exhaustChamber, passage: exhaustPassage, flow: [exhaustChamber, ...exhaustDetour, ...exhaustPassage.slice(1)] },
  };
}
/** Port-side injection chosen only to teach the route; not B58 injector CAD. */
export function fuelRouteAnchors(index, explode = 0) {
  const ports = headPortAnchors(index, explode);
  const x = cylinderX(index), lift = Math.max(0, Math.min(1, explode)) * .18;
  const nozzle = ports.intake.passage[1];
  const nozzleHeight = .012, injectorHeight = .066;
  const nozzleTop = [x, nozzle[1] + nozzleHeight, nozzle[2]];
  const injectorTop = [x, nozzleTop[1] + injectorHeight, nozzle[2]];
  const rail = [x, 1.184 + lift, nozzle[2]];
  return { rail, injectorTop, injectorHeight, injectorCenter: [x, nozzleTop[1] + injectorHeight / 2, nozzle[2]],
    nozzleTop, nozzle, nozzleHeight, nozzleCenter: [x, nozzle[1] + nozzleHeight / 2, nozzle[2]],
    // Leave the port centre before approaching the solid stem; descend outside
    // the disc radius. The final chamber entry still agrees with the charge path.
    feed: [rail, injectorTop], flow: ports.intake.flow.slice(1), connected: ports.flowConnected };
}
export function fuelFlowAvailable(degrees, lambda, connected = true) {
  return connected && typeof lambda === 'number' && Number.isFinite(lambda) && lambda > 0 && Number.isFinite(degrees) && ((degrees % 720 + 720) % 720) < 180;
}


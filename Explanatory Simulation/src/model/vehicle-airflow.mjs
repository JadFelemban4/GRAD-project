import { turboFlowPaths } from './turbo-layout.mjs';
import { CYLINDER_COUNT, cylinderX, headPortAnchors } from './engine-ports.mjs';

/** The shared conceptual turbo is mounted inside the car's engine bay, +X forward. */
export const VEHICLE_TURBO_MOUNT = Object.freeze({ position: [2.06, 0.753, 0.62], scale: 0.22 });
export const VEHICLE_BOUNDS = Object.freeze({ x: [-3.2, 3.32], y: [0, 2.2], z: [-1.486, 1.486] });

export function mountedTurboPoint(point) {
  const { position, scale } = VEHICLE_TURBO_MOUNT;
  return [position[0] + scale * point[0], position[1] + scale * point[1], position[2] + scale * point[2]];
}

const points = (items) => items.map((point) => [...point]);
const blend = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
export const vehicleTurboAnchors = Object.freeze({
  center: mountedTurboPoint([0, 0.85, 0]),
  compressor: mountedTurboPoint([0, 0.85, 0.44]),
  compressorInlet: mountedTurboPoint(turboFlowPaths.airInlet[0]),
  compressorOutlet: mountedTurboPoint(turboFlowPaths.airCharge.at(-1)),
  turbine: mountedTurboPoint([0, 0.85, -0.44]),
  turbineInlet: mountedTurboPoint(turboFlowPaths.exhaustInlet[0]),
  turbineOutlet: mountedTurboPoint(turboFlowPaths.exhaustOutlet.at(-1)),
});

const filter = [2.76, 0.84, 0.40];
const coolerEntry = [2.56, 0.82, 0.43];
const coolerExit = [2.56, 0.82, -0.43];
const merge = [1.72, 0.98, 0.37];
const plenumCenter = [1.50, 1.06, -0.45];
const plenumPoint = index => [cylinderX(index), 1.06, -0.45];
const runnerEnd = index => [cylinderX(index), 0.93, 0.30];

/** Curves are teaching guides around the model, not CFD or measured pipe routing. */
export const vehicleAirflowPaths = Object.freeze({
  airOutside: points([[3.62, 0.80, 0.24], [3.48, 0.80, 0.25], [3.14, 0.82, 0.32], filter]),
  filterToCompressor: points([filter, [2.54, 0.84, 0.43], [2.30, 0.88, 0.60], vehicleTurboAnchors.compressorInlet]),
  compressorToCooler: points([vehicleTurboAnchors.compressorOutlet, [2.42, 1.02, 0.66], [2.52, 0.88, 0.53], coolerEntry]),
  coolerToIntake: points([coolerExit, [2.27, 0.86, -0.40], [1.95, 0.98, -0.45], plenumCenter]),
  intakePlenumLeft: points([plenumCenter, plenumPoint(0)]),
  intakePlenumRight: points([plenumCenter, plenumPoint(CYLINDER_COUNT - 1)]),
  intakeBranches: Array.from({ length: CYLINDER_COUNT }, (_, index) => points([plenumPoint(index), headPortAnchors(index).intake.head])),
  exhaustRunners: Array.from({ length: CYLINDER_COUNT }, (_, index) => points([headPortAnchors(index).exhaust.head, runnerEnd(index), blend(runnerEnd(index), merge, 0.48), merge])),
  exhaustManifoldToTurbine: points([merge, [1.80, 1.04, 0.42], vehicleTurboAnchors.turbineInlet]),
  turbineToTailpipe: points([vehicleTurboAnchors.turbineOutlet, [2.08, 0.68, 0.45], [1.55, 0.53, 0.52], [0.55, 0.48, 0.65], [-1.10, 0.49, 0.67], [-2.35, 0.53, 0.70], [-3.12, 0.57, 0.70]]),
  exhaustOutside: points([[-3.12, 0.57, 0.70], [-3.32, 0.57, 0.72], [-3.62, 0.58, 0.75]]),
});

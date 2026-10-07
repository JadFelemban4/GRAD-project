export type VehiclePoint = [number, number, number];
export type VehicleAirflowPathSet = {
  airOutside: VehiclePoint[];
  filterToCompressor: VehiclePoint[];
  compressorToCooler: VehiclePoint[];
  coolerToIntake: VehiclePoint[];
  intakePlenumLeft: VehiclePoint[];
  intakePlenumRight: VehiclePoint[];
  intakeBranches: VehiclePoint[][];
  exhaustRunners: VehiclePoint[][];
  exhaustManifoldToTurbine: VehiclePoint[];
  turbineToTailpipe: VehiclePoint[];
  exhaustOutside: VehiclePoint[];
};
export const VEHICLE_TURBO_MOUNT: Readonly<{position: VehiclePoint; scale:number}>;
export const VEHICLE_BOUNDS: Readonly<{x:[number,number];y:[number,number];z:[number,number]}>;
export const vehicleTurboAnchors: Readonly<Record<string, VehiclePoint>>;
export const vehicleAirflowPaths: Readonly<VehicleAirflowPathSet>;
export function mountedTurboPoint(point: VehiclePoint): VehiclePoint;

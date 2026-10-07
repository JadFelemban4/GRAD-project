export type EnginePoint = [number, number, number];
export const CYLINDER_COUNT: number;
export const CYLINDER_BORE: Readonly<{z: number; y: number; radius: number; height: number}>;
export function cylinderX(index: number): number;
export type HeadPort = {head: EnginePoint; valve: EnginePoint; chamber: EnginePoint; passage: EnginePoint[]; flow: EnginePoint[]};
export function headPortAnchors(index: number, explode?: number): {
  bore: {center: EnginePoint; radius: number; height: number};
  flowConnected: boolean;
  intake: HeadPort;
  exhaust: HeadPort;
};
export function fuelRouteAnchors(index: number, explode?: number): {
  rail: EnginePoint; injectorTop: EnginePoint; injectorHeight: number; injectorCenter: EnginePoint;
  nozzleTop: EnginePoint; nozzle: EnginePoint; nozzleHeight: number; nozzleCenter: EnginePoint;
  feed: EnginePoint[]; flow: EnginePoint[]; connected: boolean;
};
export function fuelFlowAvailable(degrees: number, lambda: unknown, connected?: boolean): boolean;
export const VALVE_GEOMETRY: Readonly<{discRadius:number; discHeight:number; stemRadius:number; stemHeight:number; stemOffset:number; lift:number}>;
export const FUEL_GEOMETRY: Readonly<{tubeRadius:number; packetRadius:number; arrowRadius:number; arrowHeight:number; arrowStations:readonly number[]}>;
export const GAS_GEOMETRY: Readonly<{packetRadius:number; arrowRadius:number; arrowHeight:number; arrowStations:readonly number[]}>;
export function gasFlowCurve(points: EnginePoint[]): import('three').CurvePath<import('three').Vector3>;
export function gasFlowAvailable(degrees:number, side:'intake'|'exhaust', connected?:boolean, muted?:boolean):boolean;

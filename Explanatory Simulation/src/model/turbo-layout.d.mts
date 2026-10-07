export type TurboFlowPath = [number, number, number][];
export type TurboFlowData = { air: number | null; exhaust: number | null };
export const TURBO_CENTER: [number, number, number];
export const turboAnchors: {
  [part: string]: [number, number, number];
  compressor: [number, number, number];
  'compressor-housing': [number, number, number];
  turbine: [number, number, number];
  'turbo-shaft': [number, number, number];
  'turbo-housing': [number, number, number];
};
export const turboFlowPaths: Record<'airInlet' | 'airCharge' | 'exhaustInlet' | 'exhaustOutlet', TurboFlowPath>;
export function turboFlowData(frame: any): TurboFlowData;
export function flowVisual(rate: unknown): { speed: number; density: number } | null;
export function turboHousingPosition(side: 'compressor' | 'turbine', explode?: number): [number, number, number];

export function advanceTurboPhase(phase:number,elapsed:number,rate:number):number;

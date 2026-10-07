export type ThermalNode = 't_block' | 't_oil' | 't_turb';

export type ThermalPath = {
  id: string;
  from: string;
  to: string;
  state: 'active' | 'inactive' | 'equal' | 'unknown';
};

export const thermalAnchors: Record<string, [number, number, number]>;
export const thermalNames: Record<string, string>;

export function thermalLesson(frame: any, selected: string): {
  node: ThermalNode;
  paths: ThermalPath[];
  regulator: number | null;
};

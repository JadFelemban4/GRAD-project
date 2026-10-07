export type OperatingInputs = { rpm: number; map_kpa: number; spark: number; lam: number };
export type PlantReadings = {
  torque_nm?: unknown;
  egt_c?: unknown;
  mdot_fuel_gps?: unknown;
  mdot_air_gps?: unknown;
};
export type SuccessfulOperatingSnapshot = { inputs: OperatingInputs; result: PlantReadings };
export type OperatingBaseline = Readonly<{
  inputs: Readonly<OperatingInputs>;
  result: Readonly<{ torque_nm: number | null; egt_c: number | null; mdot_fuel_gps: number | null; mdot_air_gps: number | null }>;
}>;
export type OperatingComparisonRow = Readonly<{
  key: 'torque_nm' | 'egt_c' | 'mdot_fuel_gps' | 'mdot_air_gps';
  baseline: number | null;
  current: number | null;
  delta: number | null;
  unit: 'Nm' | '°C' | 'g/s';
}>;
export const operatingChannels: readonly Readonly<{ key: OperatingComparisonRow['key']; unit: OperatingComparisonRow['unit'] }>[];
export function captureOperatingBaseline(successfulSnapshot: SuccessfulOperatingSnapshot | null | undefined): OperatingBaseline | null;
export function compareOperatingResults(currentResult: PlantReadings | null | undefined, baseline: OperatingBaseline | null | undefined): OperatingComparisonRow[];

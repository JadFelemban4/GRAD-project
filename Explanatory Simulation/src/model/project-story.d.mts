export const PREVIEW_HORIZONS_S: readonly number[];
export const PHYSICAL_CONTROLS: readonly Readonly<{
  id: string;
  index: number;
  label: string;
  unit: string;
  digits: number;
}>[];
export type ProjectStorySlot = { seconds: number; gradePct: number | null };
export type ProjectStoryControl = { id: string; label: string; unit: string; digits: number; value: number | null };
export type ProjectStoryData = {
  torqueErrorNm:number|null;
  observedTorqueReqNm: number | null;
  outputs: Record<string, number | null>;
  memory: {id:string;label:string;beforeC:number|null;afterC:number|null;deltaC:number|null}[];
  previousMatches:boolean;
  damageRate:number|null; totalDamage:number|null; reward:number|null;
  rewardFields:Record<string,number|null>;
  currentGradePct: number | null;
  inputTimeS: number;
  previewSlots: ProjectStorySlot[];
  torqueReqNm: number | null;
  egtC: number | null;
  turbineC: number | null;
  timeline: {inputS: number; endS: number; hasAppliedAction: boolean; intervalEgtC: number | null; endTurbineC: number | null};
  controls: ProjectStoryControl[];
};
export function buildProjectStory(
  frame: Record<string, any> | null | undefined,
  options?: { preview?: boolean; road?: { time_s: number[]; grade_pct: number[] }; time?: number; previousFrame?: Record<string,any>|null; sessionId?:string; previousSessionId?:string },
): ProjectStoryData;

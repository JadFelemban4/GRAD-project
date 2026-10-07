import type { ProjectStoryData } from './project-story.mjs';
export type ControllerRole = 'policy'|'ecu'|'engine'|'thermal'|'reward';
export function relativeReduction(value:unknown,reference:unknown):number|null;
export function roleFor(quantity:string):ControllerRole;
export function roleSequence(story:ProjectStoryData):ControllerRole[];
export function decisionOutcome(frame:any,story:ProjectStoryData):{demand:number|null;torque:number|null;errorNm:number|null;errorPct:number|null;baselineTorque:number|null;fuel:number|null;baselineFuel:number|null;fuelReductionPct:number|null;damageRate:number|null;baselineDamageRate:number|null;intervalDamage:number|null;totalDamage:number|null;baselineTotalDamage:number|null;damageReductionPct:number|null;totalFuel:number|null;baselineTotalFuel:number|null;weights:(number|null)[];terms:(number|null)[];weightedSubtotal:number|null;uncertainty:number|null;smoothness:number|null;complete:boolean;reconstructed:number|null;reward:number|null};

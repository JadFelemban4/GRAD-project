export const routes: Record<'air'|'charge'|'exhaust'|'tail'|'coolant'|'oil',[number,number,number][]>;
export function cylinderPose(phase:number):{pinY:number;pinZ:number;jointY:number;pistonY:number};

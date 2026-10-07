export type PressureReading = {value:number|null;normalized:number|null;inputS:number|null;source:string};
export type PressurePoint = {id:string;value:number|null;gaugeKpa:number|null;timeS:number|null};
export function pressureReading(frame:any, sessionId?:string):PressureReading;
export function pressurePoints(frame:any, sessionId?:string):PressurePoint[];

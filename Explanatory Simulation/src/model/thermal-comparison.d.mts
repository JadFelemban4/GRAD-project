export type ThermalRequest = {rpm:number;map_kpa:number;ambient_c:number;spark:number;lam:number;fan:number;pump:number;heat_s:number;cool_s:number};
export type ThermalRun = {readonly request:ThermalRequest;readonly frames:any[];readonly method:string;readonly initial_state:string};
export function snapshot(request:ThermalRequest,response:any):ThermalRun;
export function comparison(reference:ThermalRun|null,current:ThermalRun|null):{valid:boolean;changed:string[];invalid:string[]};
export function sharedAt(reference:any[],current:any[],time:number):null|{time:number;values:Record<string,{reference:number|null;current:number|null;delta:number|null}>};
export function axis(reference:any[],current:any[],node:string):{min:number;max:number;timeMax:number};
export function restoreReference(reference:ThermalRun):{run:ThermalRun;draft:ThermalRequest};
export function requestGate():{begin:()=>number;accept:(version:number)=>boolean;cancel:()=>void};

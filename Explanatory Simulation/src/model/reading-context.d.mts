import type { ReadingContext } from '../types';
export function resolveReading(context: ReadingContext | null | undefined, options: {frame:any;previousFrame?:any;sessionId:string;previousSessionId?:string;conceptId:string;preview?:boolean;road?:any;time?:number}): (ReadingContext & {value:number|null;inputS:number;endS:number}) | null;

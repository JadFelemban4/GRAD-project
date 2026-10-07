export function commandChains(frame:any):Array<{id:string;index:number;label:string;unit:string;digits:number;baseline:number|null;requested:number|null;applied:number|null;final:number|null;finalUnit:string;dt:number|null}>;
export function referenceDraft():number[];
export function editorDisabled(policy:string,comparison:boolean,busy:boolean):boolean;
export function editDraft(draft:number[],index:number,value:number,action:any):number[];
export function stepControls(policy:string,comparison:boolean,draft:number[]):{trims:number[]}|undefined;
import type { ReadingContext } from '../types';
export function commandReadings(chain:ReturnType<typeof commandChains>[number],sessionId:string):Array<ReadingContext & {key:'baseline'|'requested'|'applied'|'final'}>;
export function editorPresentation(activePolicy:string,comparison:boolean,busy:boolean):{showEditor:boolean;disabled:boolean;message:string};

import type { Language } from './preferences.mjs';
export const UI_COPY: Readonly<Record<string,string>>;
export function uiText<T>(value:T,language:Language):T;
export function templateText(ar:string,en:string,language:Language,values:unknown[]):string;

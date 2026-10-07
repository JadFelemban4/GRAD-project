import { createContext } from 'react';
/** Shared illustrative clock; does not change the physical plant's dt. */
export const SceneClock = createContext({time:0,cycle:0});

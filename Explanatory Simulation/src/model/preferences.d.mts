export type Language = 'ar' | 'en';
export type Theme = 'dark' | 'light';
export interface Preferences { language: Language; theme: Theme }
export const PREFERENCES_KEY: string;
export function normalizePreferences(value: unknown): Preferences;
export function readPreferences(storage?: Pick<Storage, 'getItem'>): Preferences;
export function writePreferences(storage: Pick<Storage, 'setItem'> | undefined, value: unknown): boolean;
export function updatePreferences<T extends Preferences>(current: T, patch: Partial<Preferences>): T;
export function documentPreferences(value: unknown): Preferences & { direction: 'rtl'|'ltr'; title: string; themeColor: string };
export function createLocaleCatalogCache<T>(fetchCatalog: (language: Language) => Promise<T>): (language: Language) => Promise<T>;

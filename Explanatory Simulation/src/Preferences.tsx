import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { documentPreferences, readPreferences, updatePreferences, writePreferences } from './model/preferences.mjs';
import type { Language, Theme } from './model/preferences.mjs';
type PreferenceContext = { language: Language; theme: Theme; direction: 'rtl'|'ltr'; setLanguage: (language: Language) => void; setTheme: (theme: Theme) => void; t: (ar: string, en: string) => string };
const Context = createContext<PreferenceContext | null>(null);
function storage() { try { return window.localStorage; } catch { return undefined; } }
export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState(() => readPreferences(storage()));
  useEffect(() => {
    const display = documentPreferences(preferences);
    document.documentElement.lang = display.language;
    document.documentElement.dir = display.direction;
    document.documentElement.dataset.theme = display.theme;
    document.title = display.title;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', display.themeColor);
    writePreferences(storage(), preferences);
  }, [preferences]);
  const value = useMemo<PreferenceContext>(() => ({ ...preferences, direction: preferences.language === 'ar' ? 'rtl' : 'ltr', setLanguage: language => setPreferences(current => updatePreferences(current, { language })), setTheme: theme => setPreferences(current => updatePreferences(current, { theme })), t: (ar, en) => preferences.language === 'ar' ? ar : en }), [preferences]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function usePreferences() {
  const value = useContext(Context);
  if (!value) throw new Error('usePreferences must be used inside PreferencesProvider');
  return value;
}
export function PreferenceControls() {
  const { language, theme, setLanguage, setTheme, t } = usePreferences();
  return <div className="preference-controls"><label><span>{t('اللغة', 'Language')}</span><select aria-label={t('لغة الواجهة', 'Interface language')} value={language} onChange={event => setLanguage(event.target.value as Language)}><option value="ar">العربية</option><option value="en">English</option></select></label><button aria-label={t('تبديل المظهر', 'Toggle theme')} aria-pressed={theme === 'dark'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? t('مظهر فاتح', 'Light theme') : t('مظهر داكن', 'Dark theme')}</button></div>;
}

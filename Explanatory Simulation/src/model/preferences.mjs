export const PREFERENCES_KEY = 'supra-lab-preferences';
export function normalizePreferences(value) {
  return { language: value?.language === 'en' ? 'en' : 'ar', theme: value?.theme === 'light' ? 'light' : 'dark' };
}
export function readPreferences(storage) {
  try { return normalizePreferences(JSON.parse(storage.getItem(PREFERENCES_KEY))); } catch { return normalizePreferences(null); }
}
export function writePreferences(storage, value) {
  try { storage.setItem(PREFERENCES_KEY, JSON.stringify(normalizePreferences(value))); return true; } catch { return false; }
}
export function updatePreferences(current, patch) {
  return { ...current, language: ['ar','en'].includes(patch.language) ? patch.language : current.language, theme: ['dark','light'].includes(patch.theme) ? patch.theme : current.theme };
}
export function documentPreferences(value) {
  const { language, theme } = normalizePreferences(value);
  return { language, theme, direction: language === 'ar' ? 'rtl' : 'ltr', title: language === 'ar' ? 'مختبر السوبرا | تعلّم مشروعك' : 'Supra Lab | Learn your project', themeColor: theme === 'dark' ? '#0e141c' : '#edf0e8' };
}
export function createLocaleCatalogCache(fetchCatalog) {
  const cache = new Map();
  return language => {
    if (!cache.has(language)) {
      const pending = Promise.resolve().then(() => fetchCatalog(language)).catch(error => { cache.delete(language); throw error; });
      cache.set(language, pending);
    }
    return cache.get(language);
  };
}

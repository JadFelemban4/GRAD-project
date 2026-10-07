import { usePreferences } from './Preferences';
import { format as formatValue, humanMessage } from './types';
import { uiText, templateText } from './model/ui-copy.mjs';
/** Presentation translation is evaluated with current React preferences on each render. */
export function useUI() {
  const { language, direction } = usePreferences();
  return {
    direction,
    language,
    format: (value:unknown,digits=1) => formatValue(value,digits,language),
    number: (value:unknown,digits=0) => formatValue(value,digits,language),
    message: (value:unknown) => humanMessage(value, language),
    ui: <T,>(value: T): T => uiText(value, language),
    uiTemplate: (ar: string, en: string, ...values: unknown[]) => templateText(ar, en, language, values),
  };
}

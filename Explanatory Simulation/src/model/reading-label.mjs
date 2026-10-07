import { uiText, templateText } from './ui-copy.mjs';
import { PREVIEW_HORIZONS_S } from './project-story.mjs';
/** Rebuild semantic labels from retained field identity, independent of the language used when selected. */
export function readingLabel(context, language) {
  const [collection, key, member] = context.field.split('.');
  if (collection === 'previewSlots') return templateText('ميل الطريق بعد {0} ثانية', 'Road grade after {0} seconds', language, [PREVIEW_HORIZONS_S[Number(key)]]);
  if (collection === 'memory') {
    const name = {t_block:'معدن المحرك',t_oil:'الزيت',t_turb:'حاوية التوربين'}[key] || key;
    return templateText(member === 'beforeC' ? '{0} عند الدخل' : '{0} عند النهاية', member === 'beforeC' ? '{0} at input' : '{0} at end', language, [name]);
  }
  if (collection === 'chains') return uiText({baseline:'مرجع ECU / حلقة المرجع',requested:'الطلب الفيزيائي',applied:'بعد حد التغيير',final:'القيمة النهائية من المصدر'}[member] || context.label, language);
  return uiText(context.label, language);
}

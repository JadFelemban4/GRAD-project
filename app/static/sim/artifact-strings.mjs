// Bilingual wording for the read-only artifact catalog/status strip.
import { STRINGS } from './i18n.mjs';

export const ARTIFACT_STRINGS = {
  ar: {
    'artifact.heading': 'ملفات التدريب والنتائج',
    'artifact.changed': 'تغيّر مصدر العرض. أُوقف العرض القديم؛ اختر المصدر ثم اضغط احسب من جديد.',
    'artifact.empty': 'لم تصل ملفات مدعومة بعد.',
    'artifact.last_valid': 'جارٍ التحديث · المعروض آخر نسخة سليمة',
    'artifact.source': 'المصدر: {path}',
    'artifact.kind.run_pair': 'مجموعة تشغيل',
    'artifact.kind.evaluation_text': 'ملخص تقييم منشور',
    'artifact.kind.agent_set': 'مجموعة وكلاء',
    'artifact.lifecycle.running': 'التدريب جارٍ',
    'artifact.lifecycle.finalizing': 'جارٍ إنهاء الملفات',
    'artifact.lifecycle.finished': 'انتهى التدريب',
    'artifact.lifecycle.published': 'ملفات منشورة',
    'artifact.lifecycle.interrupted': 'توقف التدريب',
    'artifact.lifecycle.unknown': 'حالة التدريب غير معروفة',
    'artifact.evidence.available': '{name}: متاح',
    'artifact.evidence.unavailable': '{name}: غير متاح',
    'artifact.evidence.model': 'النموذج النهائي',
    'artifact.evidence.training_curve': 'منحنى التدريب',
    'artifact.evidence.training_record': 'تسجيل التدريب',
    'artifact.evidence.evaluation_summary': 'ملخص التقييم',
    'artifact.evidence.evaluation_record': 'تسجيل التقييم',
    'artifact.evidence.verdict': 'الحكم المنشور',
    'artifact.compatibility.allowed': 'إعادة التشغيل مسموحة',
    'artifact.compatibility.refused': 'إعادة التشغيل مرفوضة: {reason}',
    'artifact.compatibility.unknown': 'توافق إعادة التشغيل غير معروف',
    'artifact.issues.none': 'لا توجد ملاحظات',
    'artifact.issues.list': 'ملاحظات: {items}',
    'artifact.reader.pending': 'عرض النتائج بانتظار قارئ مجموعة الوكلاء',
    'artifact.status.connected': 'متصل',
    'artifact.status.updating': 'جارٍ التحديث',
    'artifact.status.offline': 'الخادم غير متصل',
    'artifact.status.last_success': 'آخر تحديث ناجح: {time}',
    'artifact.status.restart_needed': 'يلزم إعادة تشغيل الخادم بعد تغيير ملفات النموذج',
    'artifact.status.restart_not_needed': 'لا يلزم إعادة تشغيل الخادم',
  },
  en: {
    'artifact.heading': 'Training and result artifacts',
    'artifact.changed': 'The replay source changed. Old playback stopped; select the source and compute again.',
    'artifact.empty': 'No supported artifacts have arrived yet.',
    'artifact.last_valid': 'Updating · showing the last valid snapshot',
    'artifact.source': 'Source: {path}',
    'artifact.kind.run_pair': 'Run group',
    'artifact.kind.evaluation_text': 'Published evaluation summary',
    'artifact.kind.agent_set': 'Agent set',
    'artifact.lifecycle.running': 'Training is running',
    'artifact.lifecycle.finalizing': 'Files are finalizing',
    'artifact.lifecycle.finished': 'Training finished',
    'artifact.lifecycle.published': 'Published evidence',
    'artifact.lifecycle.interrupted': 'Training was interrupted',
    'artifact.lifecycle.unknown': 'Training state is unknown',
    'artifact.evidence.available': '{name}: available',
    'artifact.evidence.unavailable': '{name}: unavailable',
    'artifact.evidence.model': 'final model',
    'artifact.evidence.training_curve': 'training curve',
    'artifact.evidence.training_record': 'training recording',
    'artifact.evidence.evaluation_summary': 'evaluation summary',
    'artifact.evidence.evaluation_record': 'evaluation recording',
    'artifact.evidence.verdict': 'published verdict',
    'artifact.compatibility.allowed': 'Replay is allowed',
    'artifact.compatibility.refused': 'Replay refused: {reason}',
    'artifact.compatibility.unknown': 'Replay compatibility is unknown',
    'artifact.issues.none': 'No issues reported',
    'artifact.issues.list': 'Issues: {items}',
    'artifact.reader.pending': 'Agent-set results are awaiting reader',
    'artifact.status.connected': 'Connected',
    'artifact.status.updating': 'Updating',
    'artifact.status.offline': 'Server offline',
    'artifact.status.last_success': 'Last successful update: {time}',
    'artifact.status.restart_needed': 'Restart the server after changing plant files',
    'artifact.status.restart_not_needed': 'No server restart needed',
  },
};

export function mergeArtifactStrings(target, extra) {
  const langs = Object.keys(target);
  for (const lang of Object.keys(extra)) {
    if (!langs.includes(lang)) throw new Error(`artifact strings: unknown language "${lang}"`);
  }
  const keys = new Set(Object.values(extra).flatMap(table => Object.keys(table)));
  for (const lang of langs) {
    const table = extra[lang] ?? {};
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(table, key)) {
        const present = Object.keys(extra).filter(code => Object.prototype.hasOwnProperty.call(extra[code], key));
        throw new Error(`artifact strings: "${key}" is missing from ${lang} (present in ${present.join(', ')})`);
      }
      if (Object.prototype.hasOwnProperty.call(target[lang], key)) {
        throw new Error(`artifact strings: "${key}" collides with an existing ${lang} string`);
      }
    }
  }
  for (const lang of langs) Object.assign(target[lang], extra[lang]);
  return keys.size;
}

mergeArtifactStrings(STRINGS, ARTIFACT_STRINGS);

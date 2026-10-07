import { uiText } from './model/ui-copy.mjs';
import type { Language } from './model/preferences.mjs';
export type Mode = 'studio' | 'tour' | 'sandbox' | 'trace' | 'viva';
export type Source = { file: string; symbol?: string; variable?: string; line: number };
export type Concept = { id: string; name: string; meaning: string; why: string; unit?: string; evidence: string; range?: unknown; source: Source; upstream: string[]; downstream: string[]; increase?: string; decrease?: string; caveat?: string };
export type Lesson = { id: string; title: string; subtitle?: string; body: string; experiment: string; layer: string; focus: string; concepts: string[] };
export type Meta = { vehicle: any; actions: any[]; observations: any[]; preview_s: number[]; thresholds: any; concepts: Concept[]; tour: Lesson[]; viva: any[]; scenarios: any[]; derived: any; limitations: string[] };
export type Frame = { time_s: number; rpm: number; map_kpa: number; speed_kmh: number; grade_pct: number; gear: number; torque_req: number; torque: number; egt_c: number | null; t_turb: number; t_oil: number; t_block: number; spark: number; lam: number; mdot_fuel: number; mdot_air: number; ki: number; damage_rate: number; reward: number; r_resp: number; r_fuel: number; r_life: number; cost_torque: number; cost_knock: number; cost_egt: number; action: number[]; command: number[]; obs: number[]; obs_in: number[]; preview_pct: number[]; baseline: any; totals: any; [key: string]: any };
export type Road = { time_s: number[]; grade_pct: number[]; speed_kmh: number[] };

const evidenceArabic: Record<string, string> = {
  MEASURED: 'مقاس فعليًا', MODELLED: 'محاكاة', MODELED: 'محاكاة',
  DERIVED: 'مستخرج من البيانات', ASSUMED: 'افتراض', UNVALIDATED: 'غير متحقق منه',
  UNVERIFIED: 'إعادة تشغيل غير موثقة', UNAVAILABLE: 'غير متاح',
  'SCENARIO INPUT': 'مدخل التجربة', PUBLISHED: 'منشور', STATISTIC: 'نتيجة إحصائية',
  MIXED: 'مصادر مختلطة',
};
export function evidenceLabel(value?: string, language: Language = 'ar') {
  const key = value?.trim().toUpperCase() || 'UNVERIFIED';
  return uiText(evidenceArabic[key] || key, language);
}

const messages: Record<string, string> = {
  'This MAP is outside the 30–75 kPa range of the documented 26-point air-filling/air-mass residual comparison; that check does not establish accuracy here.': 'ضغط المانيفولد خارج نطاق 30–75 kPa الذي شملته مقارنة تعبئة الهواء وتدفقه في 26 نقطة؛ هذه المقارنة لا تثبت دقة النتيجة هنا.',
  'Requested MAP exceeds the log-derived vehicle operating ceiling at this model-predicted airflow; this direct engine-lab point is not vehicle-feasible.': 'ضغط المانيفولد المطلوب يتجاوز الحد التشغيلي المستنتج من السجلات عند تدفق الهواء الذي يتنبأ به النموذج؛ هذه النقطة ليست حالة ممكنة للمركبة.',
  'Requested MAP is near the log-derived vehicle operating ceiling at this model-predicted airflow.': 'ضغط المانيفولد المطلوب قريب من الحد التشغيلي المستنتج من السجلات عند تدفق الهواء الذي يتنبأ به النموذج.',
  'simulation session capacity reached': 'بلغت المحاكاة الحد الأقصى للجلسات المفتوحة. أعد ضبط جلسة أو أغلقها.',
  'simulation session is complete; create a new session': 'انتهت هذه الجلسة. ابدأ جلسة جديدة للمتابعة.',
  'unknown or expired session': 'جلسة المحاكاة غير موجودة أو انتهت.',
  'unknown recording': 'التسجيل المحدد غير موجود.',
  'catalog is not ready': 'بيانات المشروع غير جاهزة بعد.',
  'replay support is unavailable': 'ميزة إعادة تشغيل التسجيل غير متاحة.',
  'Actor weights have no fatal source-code fingerprint; this rerun is not a scored evaluation.': 'لا يتوفر للوكيل بصمة كاملة لهوية الشيفرة؛ إعادة التشغيل هذه تعليمية وليست نتيجة تقييم مسجلة.',
  'The paired preview CI spans zero; this is inconclusive, not evidence of no effect.': 'يشمل فاصل الثقة المقترن للصعود الصفر؛ لذا فالنتيجة غير حاسمة، ولا تثبت غياب الأثر.',
  'The sighted and blind actor files are exported policy weights, not the exact scored final.zip artefacts.': 'ملفات الوكلاء المطلعة والعمياء أوزان مُصدّرة للسياسة، وليست ملفات final.zip نفسها التي خضعت للتقييم المسجل.',
  'The terrain_dt1 training config records a data fingerprint but no plant_sha; actor replays are UNVERIFIED.': 'يسجل إعداد التدريب بصمة البيانات ولا يتضمن plant_sha؛ لذلك فإعادة تشغيل الوكيل غير موثقة.',
  'Most of the trained agents’ apparent advantage over hand-written policies depends on the unvalidated knock model.': 'يعتمد معظم التفوق الظاهر للوكلاء المدرّبين على السياسات المكتوبة يدويًا على نموذج طرق غير متحقق منه.',
  'The turbine node is modelled from assumed constants and has no matching car sensor.': 'تُحاكى عقدة التوربين بثوابت مفترضة ولا يقابلها حساس في السيارة.',
  'The simulator’s thermal block/coolant update oscillates at dt=1 s; H/tau sweep claims remain unquotable.': 'يتذبذب تحديث الكتلة وسائل التبريد عند dt=1 s؛ لذلك لا يصح الاستشهاد بنتائج مسح H/τ حاليًا.',
  'The integrated damage value is a proxy and is not a prediction of real component lifetime.': 'قيمة الضرر المتكاملة مؤشر تقريبي وليست تنبؤًا بالعمر الفعلي للمكونات.',
};

function humanWarningArabic(value: unknown): string {
  const text = typeof value === 'string' ? value : '';
  if (!text) return 'تحذير من النموذج؛ افتح المصدر للاطلاع على التفاصيل.';
  if (messages[text]) return messages[text];
  if (Object.values(messages).includes(text)) return text;
  if (text.startsWith('The source plant returned non-finite diagnostics:')) return 'أعاد نموذج المحرك قيَمًا غير منتهية في بعض المخرجات؛ راجع نقطة التشغيل أو المصدر.';
  if (text.startsWith('This MAP is outside')) return messages['This MAP is outside the 30–75 kPa range of the documented 26-point air-filling/air-mass residual comparison; that check does not establish accuracy here.'];
  if (text.startsWith('Requested MAP exceeds')) return messages['Requested MAP exceeds the log-derived vehicle operating ceiling at this model-predicted airflow; this direct engine-lab point is not vehicle-feasible.'];
  if (text.startsWith('Requested MAP is near')) return messages['Requested MAP is near the log-derived vehicle operating ceiling at this model-predicted airflow.'];
  if (/UNVERIFIED|UNVALIDATED|inconclusive|fingerprint|knock model|damage proxy/i.test(text)) return 'تنبيه علمي: راجع المصدر والتفاصيل قبل تفسير هذه النتيجة.';
  return 'تحذير من النموذج؛ افتح المصدر للاطلاع على التفاصيل.';
}

function humanMessageArabic(value: unknown): string {
  const text = typeof value === 'string' ? value : '';
  if (!text) return 'تعذّر إكمال الطلب. حاول مرة أخرى.';
  if (messages[text]) return messages[text];
  if (/^unsupported controls:/.test(text)) return 'أحد مدخلات التحكم غير مدعوم.';
  if (/^(steps|speed_kmh|grade_pct|ambient_c|seed|trims) must /.test(text)) return 'قيمة أحد المدخلات غير صالحة أو خارج الحدود.';
  if (/outside the physical action bounds|outside the .* action bounds/.test(text)) return 'قيم المشغلات تتجاوز حدودها الفيزيائية.';
  if (/derived-data fingerprint|no readable|unsupported SAC actor|architecture/.test(text)) return 'تعذّر تحميل هذا الوكيل أو لم تتطابق بياناته مع نسخة المشروع الحالية.';
  if (text === 'Simulation transport failed' || text.startsWith('Simulation request failed')) return 'تعذّر الاتصال بالمحاكاة. تحقّق من تشغيل الخدمة المحلية.';
  if (text.startsWith('source is not allowlisted') || text.startsWith('source file')) return 'لا يسمح بعرض هذا المصدر.';
  return humanWarningArabic(text);
}

export function humanWarning(value: unknown, language: Language = 'ar'): string { return uiText(humanWarningArabic(value), language); }
export function humanMessage(value: unknown, language: Language = 'ar'): string { return uiText(humanMessageArabic(value), language); }

export function localizedLabel(value: string, language: Language = 'ar') {
  const labels: Record<string, string> = {
    'Vehicle speed': 'سرعة المركبة', 'Road grade': 'ميل الطريق',
    'Ambient temperature': 'درجة حرارة الجو', 'Spark trim': 'تعديل توقيت الشرارة',
    'Lambda trim': 'تعديل لامدا', 'MAP trim': 'تعديل ضغط المانيفولد',
    'Radiator fan duty': 'سرعة مروحة الرديتر', 'Coolant pump duty': 'سرعة مضخة التبريد',
    'Spark advance': 'تقديم الشرارة', 'Manifold pressure': 'ضغط المانيفولد',
    'Heating duration': 'مدة التسخين', 'RPM': 'سرعة المحرك', 'Lambda': 'لامدا',
  };
  return language === "en" ? value : labels[value] || value;
}

type ConceptCopy = Pick<Concept, 'name' | 'meaning' | 'why' | 'caveat' | 'increase' | 'decrease'>;
export function conceptCopy(concept: Concept): ConceptCopy {
  return { name: concept.name, meaning: concept.meaning, why: concept.why, caveat: concept.caveat, increase: concept.increase, decrease: concept.decrease };
}

export async function api<T = any>(path: string, body?: unknown, method?: string): Promise<T> {
  const init: RequestInit | undefined = method === 'DELETE' ? { method } : body === undefined ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  let res: Response;
  try { res = await fetch(`/api/${path}`, init); }
  catch (cause) { throw new Error('Simulation transport failed', { cause }); }
  if (!res.ok) { const value = await res.json().catch(() => ({})); throw new Error(typeof value.detail === 'string' ? value.detail : `Simulation request failed (${res.status})`); }
  return res.json();
}
export const format = (x: unknown, digits = 1, language: Language = 'ar') => typeof x === 'number' && Number.isFinite(x) ? x.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits }) : uiText('غير متاح', language);
export function valueAt(frame: Frame | null | undefined, key: string, offset = 0): number | undefined { const value = frame?.[key]; return typeof value === 'number' && Number.isFinite(value) ? value - offset : undefined; }
export type ReadingContext = { conceptId: string; field: string; phase: 'baseline' | 'requested' | 'input' | 'applied' | 'interval' | 'end'; label: string; unit: string; digits: number; sessionId: string };

/** General viva catalog permits one target or several; the Inspector requires one stable ID. */
export function vivaFocus(question: { focus?: string | string[] } | undefined, concepts: Pick<Concept, "id">[]): string {
  const targets = Array.isArray(question?.focus) ? question.focus : [question?.focus];
  return targets.find(id => typeof id === "string" && concepts.some(concept => concept.id === id)) || "agent";
}

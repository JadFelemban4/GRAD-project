import { graphicsText } from './graphics-strings.mjs?v=R1a';
const STRINGS={
  heading:['Saved decisions','القرارات المحفوظة'],intro:['Inspect a saved training or evaluation record. Select a source, policy and episode.','افحص تسجيل تدريب أو تقييم محفوظًا. اختر المصدر والسياسة والحلقة.'],
  source:['Source / experiment','المصدر / التجربة'],record:['Policy and recording','السياسة والتسجيل'],episode:['Episode (zero-based)','الحلقة (تبدأ من صفر)'],choose:['Choose…','اختر…'],
  training:['Training record','تسجيل التدريب'],evaluation:['Evaluation record','تسجيل التقييم'],missing:['The saved file is absent. Summary results remain available; playback needs this file.','ملف التسجيل غير موجود. الملخصات متاحة؛ إعادة العرض تحتاج هذا الملف.'],
  available:['Available recordings','التسجيلات المتاحة'],expected:['Expected recordings','التسجيلات المتوقعة'],loading:['Reading the saved recording…','جارٍ قراءة التسجيل المحفوظ…'],
  provenance:['Recorded generation','الجيل المسجل'],unknown:['Unknown; no current-plant compatibility claim','غير معروف؛ لا يوجد ادعاء توافق مع المحاكي الحالي'],
  scope:['One policy and episode at a time. Pair alignment has not been established.','سياسة وحلقة واحدة في كل مرة. لم تُثبت محاذاة التسجيلات للمقارنة بين وكيلين.'],
  phase:['Observations and commands precede the step; applied actions, rewards and engine outcomes follow it. The cursor identifies the same saved sample, with these phases kept distinct.','الملاحظات والأوامر قبل الخطوة؛ الأفعال المطبّقة والمكافآت وحالة المحرك بعدها. المؤشر يحدد العينة المحفوظة نفسها مع إبقاء المرحلتين واضحتين.'],
  before_step:['Before step','قبل الخطوة'],after_step:['After step','بعد الخطوة'],command:['Issued command','الأمر المطلوب'],applied:['Applied action','الفعل المطبّق'],actuator:['Actuator','المشغّل'],
  normalized:['Normalized policy input / command','دخل أو أمر السياسة المطبّع'],physical:['Recorded physical applied value','القيمة الفيزيائية المطبّقة المسجلة'],
  sample:['Selected source sample','عينة المصدر المختارة'],window:['Visible sample window','نافذة العينات المعروضة'],time:['Recorded time','الزمن المسجل'],step_axis:['Timing is unavailable; the horizontal axis is the recorded sample index. Playback advances samples, without assigning seconds.','التوقيت غير متاح؛ المحور الأفقي فهرس العينة المسجل. التشغيل ينتقل بين العينات دون تعيين ثوانٍ.'],
  previous:['Previous sample','العينة السابقة'],next:['Next sample','العينة التالية'],play:['Play recording','تشغيل التسجيل'],pause:['Pause','إيقاف مؤقت'],seek:['Recorded sample index','فهرس العينة المسجلة'],
  values:['All channels at this sample','كل القنوات في هذه العينة'],channel:['Channel','القناة'],value:['Recorded value','القيمة المسجلة'],unit:['Unit','الوحدة'],phase_col:['Step phase','مرحلة الخطوة'],evidence:['Evidence','نوع الدليل'],
  missing_channel:['Not recorded','غير مسجل'],source_changed:['The recording or its source metadata changed. Select it again to load the new generation.','تغيّر التسجيل أو بيانات مصدره. اختره مجددًا لتحميل الجيل الجديد.'],
  observation:['Observed inputs','المدخلات المرصودة'],preview:['Recorded road preview','استشراف الطريق المسجل'],reward:['Recorded reward components','مكونات المكافأة المسجلة'],thermal:['Recorded thermal channels','القنوات الحرارية المسجلة'],engine:['Recorded engine outcomes','حالة المحرك المسجلة'],events:['Recorded events','الأحداث المسجلة'],
  mechanical:['Engine paths at the selected sample','مسارات المحرك عند العينة المختارة'],schematic:['Schematic geometry and rotation. Blue: intake; amber: exhaust; violet: cooling. Gases remain separate; the shaft transfers rotation. Temperature overlays use recorded channels only.','هندسة ودوران تخطيطيان. الأزرق: السحب؛ الكهرماني: العادم؛ البنفسجي: التبريد. الغازان منفصلان؛ العمود ينقل الدوران. مؤشرات الحرارة من القنوات المسجلة فقط.'],
  overview:['Whole engine','المحرك كاملًا'],turbo:['Turbo and shaft','التوربو والعمود'],intake:['Intake / exhaust','السحب والعادم'],cooling:['Cooling paths','مسارات التبريد'],
  fallback:['3D is unavailable. The path diagram and all recorded values, timeline controls and selected sample remain available below.','العرض ثلاثي الأبعاد غير متاح. مخطط المسارات والقيم المسجلة والتحكم بالزمن والعينة المختارة متاحة أدناه.'],
  reduced:['Reduced motion: schematic rotation is paused.','تقليل الحركة: الدوران التخطيطي متوقف.'],
  turbine_c:['Turbine housing °C','غلاف التوربين °C'],oil_c:['Oil °C','الزيت °C'],block_c:['Block °C','كتلة المحرك °C'],coolant_c:['Coolant °C','سائل التبريد °C'],
  compressor:['Compressor','الضاغط'],turbine:['Turbine','التوربين'],shaft:['Shaft (rotation only)','العمود (دوران فقط)'],air_in:['Fresh air → compressor → engine','هواء نقي ← الضاغط ← المحرك'],gas_out:['Engine exhaust → turbine → outlet','عادم المحرك ← التوربين ← المخرج'],cooling_flow:['Engine ↔ pump ↔ radiator / fan','المحرك ↔ المضخة ↔ المبرّد / المروحة'],
  no_records:['No saved-record sources were discovered.','لم تُكتشف مصادر تسجيلات محفوظة.'],error:['Recording could not be read','تعذّر قراءة التسجيل'],
  'normalized_policy_command[-1,1]':['Normalized policy command [−1, 1]','أمر السياسة المطبّع [−1، 1]'],
  physical_applied_after_slew_limit:['Physical applied action after slew limiting','فعل فيزيائي بعد قيد سرعة التغيير'],
  normalized_policy_input:['Normalized policy input','دخل السياسة المطبّع'],
  recorded_policy_input:['Recorded policy input','دخل السياسة المسجل'],
  recorded_engine_state:['Recorded engine state','حالة المحرك المسجلة'],
  recorded_reward:['Recorded reward','المكافأة المسجلة'],
  recorded_reward_component:['Recorded reward component','مكوّن المكافأة المسجل'],
  recorded_damage_rate_unit_unspecified:['Recorded damage rate; unit unspecified','معدل ضرر مسجل دون تحديد الوحدة'],
  recorded_event:['Recorded event','حدث مسجل'],
};
const LABELS={
  'Spark trim command':'أمر تعديل الإشعال','Lambda trim command':'أمر تعديل لامبدا','Boost trim command':'أمر تعديل الشحن','Fan duty command':'أمر تشغيل المروحة','Pump duty command':'أمر تشغيل المضخة',
  'Spark trim applied':'تعديل الإشعال المطبّق','Lambda trim applied':'تعديل لامبدا المطبّق','Boost trim applied':'تعديل الشحن المطبّق','Fan duty applied':'تشغيل المروحة المطبّق','Pump duty applied':'تشغيل المضخة المطبّق',
  'Turbine temperature':'حرارة التوربين','Block temperature':'حرارة كتلة المحرك','Baseline turbine temperature':'حرارة التوربين الأساسي',
  'Intake temperature':'حرارة هواء السحب','Ambient temperature':'حرارة الجو','Barometric pressure':'ضغط الجو','Humidity':'الرطوبة','Throttle':'الخانق','Vehicle speed':'سرعة السيارة',
  'Current road grade':'ميل الطريق الحالي','Torque request':'العزم المطلوب','Torque':'العزم','Reward':'المكافأة','Fuel reward':'مكافأة الوقود','Life reward':'مكافأة العمر','Responsiveness reward':'مكافأة الاستجابة',
  'Policy aggression':'اندفاع السياسة','Observation vector':'متجه الملاحظات','Exhaust gas temperature':'حرارة غاز العادم','Knock integral':'تكامل الطَّرْق','Damage rate':'معدل الضرر','Fuel flow':'تدفق الوقود',
  Spark:'توقيت الإشعال',
  normalized:'مطبّع','normalized [-1,1]':'مطبّع [−1، 1]',K:'كلفن',kPa:'كيلوباسكال',
  normalized_policy_input:'دخل السياسة المطبّع',recorded_policy_input:'دخل السياسة المسجل',recorded_engine_state:'حالة المحرك المسجلة',recorded_reward:'المكافأة المسجلة',recorded_reward_component:'مكوّن المكافأة المسجل',
  'normalized_policy_command[-1,1]':'أمر السياسة المطبّع [−1، 1]',physical_applied_after_slew_limit:'فعل فيزيائي بعد قيد سرعة التغيير',
  recorded_damage_rate_unit_unspecified:'معدل ضرر مسجل دون تحديد الوحدة',recorded_event:'حدث مسجل',
};
export function recordText(lang,key){
  if(key==='missing_record')key='missing';
  if(STRINGS[key])return STRINGS[key][lang==='ar'?1:0];
  if(lang==='ar'&&LABELS[key])return LABELS[key];
  if(lang==='ar'){
    const preview=/^Road preview at (\d+) s$/.exec(key);if(preview)return `استشراف الطريق عند ${preview[1]} ثانية`;
    const observation=/^Observation (\d+)$/.exec(key);if(observation)return `الملاحظة ${observation[1]}`;
    const weight=/^Policy preference weight (\d+)$/.exec(key);if(weight)return `وزن تفضيل السياسة ${weight[1]}`;
  }
  return graphicsText(lang,key);
}

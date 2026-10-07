import { useUI } from './useUI';
import { usePreferences } from './Preferences';
import { readingProvenance, loadComparisonInputs } from './model/provenance.mjs';
import { format } from './types';
export function ProvenanceDrawer({concept,value,reading,frame,pressure,onSource}:any) {
  const { format, ui } = useUI();

 const {t}=usePreferences(); const p=readingProvenance(concept,reading,frame,pressure,value);
 const hasTime=Array.isArray(p.time)?p.time.every((v:any)=>typeof v==='number'&&Number.isFinite(v)):typeof p.time==='number'&&Number.isFinite(p.time);
 const time=hasTime?(Array.isArray(p.time)?p.time.map((v:any)=>format(v,1)).join('–'):format(p.time,1)):t('غير متاح','Unavailable');
 return <details className="provenance-drawer" data-testid="provenance-drawer"><summary>{ui(t('لماذا أثق بهذا الرقم؟','Why trust this number?'))}</summary>
 <p>{ui(t('الكمية / الموضع:','Quantity / location:'))} <code dir="ltr">{p.quantity}</code> · {ui(concept.name)}<br/>{ui(t('الوحدة والزمن:','Unit and time:'))} <bdi dir="ltr">{ui(p.unit)} · {ui(time)}{hasTime ? " s" : ""} · {ui(p.phase)}</bdi></p>
 <p>{ui(t('الأصل:','Origin:'))} {ui(({simulated:t('حساب محاكاة، وليس قراءة حساس مسجلة.','Simulation calculation, not a recorded sensor reading.'),derived:t('اشتقاق من مدخل السيناريو؛ ليس حساس ضغط مسجلًا.','Derived from scenario input; not a recorded pressure sensor.'),'recorded-statistic':t('إحصاء بحثي مسجل في ملف النتائج؛ لا توجد قراءة حية لهذه الكمية هنا.','Recorded research statistic in the results file; no live reading of this quantity is available here.'),assumption:t('افتراض في نموذج المشروع؛ لا توجد قراءة حية له هنا.','Project-model assumption; no live reading is available here.'),unavailable:t('غير متاح: لا توجد قراءة حالية لهذه الكمية.','Unavailable: no current reading of this quantity.')} as Record<string,string>)[p.origin])}</p>
 <p>{ui(t('القيمة الحالية:','Current value:'))} <bdi dir="ltr">{ui(p.available ? format(p.value, reading?.digits ?? 1) : t('غير متاحة','Unavailable'))}</bdi>. {ui(t('وسام المفهوم يصف أساسه العلمي لا أصل القراءة الحالية.','The concept badge describes its scientific basis, not the origin of this current reading.'))}</p>
 <button onClick={()=>onSource(concept.source)}><code dir="ltr">{p.source}</code></button>
 <p>{ui(t('معيار المقارنة: معيار محلي غير موثق بعد. يلزم تطابق المتغير والموضع والوحدات والظروف والزمن ومصدر المرجع قبل الحكم. حرارة غاز العادم ليست معدن التوربين؛ الزيت ليس سائل التبريد.','Comparison criterion: local criterion not yet documented. Match quantity, location, units, conditions, time and reference source before judging. Exhaust gas is not turbine metal; oil is not coolant.'))}</p>
 <h4>{ui(t('مثال تاريخي موثق: الزيت','Documented historical example: oil'))}</h4>
 <p><bdi dir="ltr">97.0 °C vs 103–111 °C</bdi> · <code>drive10</code> · {ui(t('أكثر 10 دقائق حرارة؛ النطاق الربيعي لقراءة زيت السيارة. النموذج outside، داخل بيانات الملاءمة؛ ليس اختبارًا مستقلاً ولا نطاقًا مصنعيًا ولا مقارنة بالزمن الحي. موضع الحساس الدقيق غير موثق هنا.','Hottest 10 minutes; interquartile range of the car oil reading. Model marked outside, in-sample calibration data; not independent validation, a manufacturer range or a live-time comparison. Exact sensor location is not documented here.'))}</p>
 <button onClick={()=>onSource({file:'validation_table.md',line:106})}>validation_table.md:106</button>
 <p>{ui(t('اختلاف رقمين لا يثبت خطأ الريدر أو المانيوال؛ ضوضاء الجهاز فرضية للفحص. اختبارات الواجهة ومطابقة المعادلات تختبر التنفيذ، بينما المقارنة التجريبية تختبر تمثيل الواقع ضمن استخدام محدد.','Two differing numbers do not prove the reader or manual wrong; instrument noise is a hypothesis to investigate. UI tests and equation matching check implementation; experimental comparison checks representation of reality for a defined use.'))}</p>
 <h4>{ui(t('ماذا تعني loss؟','What does loss mean?'))}</h4>
 <p>{ui(t('مثال المصدر هو residual MAPE لتطبيع الحمل، وليس MSE: الحمل النسبي المسجل load_meas وملء الأسطوانات النسبي المحاكى load_model عبر 26 نقطة عند 30–75 kPa.','The source example is residual MAPE for load normalization, not MSE: logged relative filling/load_meas and modeled relative filling/load_model across 26 points at 30–75 kPa.'))}</p>
 <p>{ui(t('مدخلا المقارنة هما الحمل النسبي، وليس خطأ MAP مباشرة.','Both comparison inputs are relative load, not direct MAP error.'))} <code dir="ltr">{loadComparisonInputs.measured} vs {loadComparisonInputs.modeled} = {loadComparisonInputs.formula}</code></p>
 <button onClick={()=>onSource({file:'compare_log.py',line:133})}>compare_log.py:133–142</button>
 <p>{ui(t('k_fit ملاءمة لمعامل تطبيع واحد؛ الاشتقاق من نسبة كثافتين في المصدر مسار منفصل، وليس اختبارًا مستقلاً للملاءمة.','k_fit fits one normalization factor; the source’s separate density-ratio derivation is a distinct path, not independent validation of that fit.'))}</p>
 <code dir="ltr">k_fit = sum(meas * mod) / sum(mod * mod)<br/>MAPE = mean(100 * abs(k_fit * mod - meas) / meas)</code>
 <p>{ui(t('هذا خطأ مقارنة بيانات؛ خسائر تدريب SAC ومكافأة التحكم معانٍ مختلفة. لا يتوفر هنا منحنى تدريب أو فاصل ثقة للريدر. حرارة المدخل محاكاة دون حساس بعد المبرد البيني.','This is data comparison error; SAC training losses and control reward are different quantities. No training curve or reader confidence interval is available here. Intake temperature is modeled without a post-intercooler sensor.'))}</p>
 <button onClick={()=>onSource({file:'compare_log.py',line:199})}>compare_log.py:199–267</button>
 <p><a href="https://standards.nasa.gov/standard/nasa/nasa-std-7009" target="_blank" rel="noreferrer">NASA-STD-7009B</a> — {ui(t('إطار منهجي لتحديد معايير قبول خاصة بالمشروع، وليس إعلان امتثال أو حدود سيارات جاهزة. البروتوكول والعتبات قرار الفريق والدكتور.','Methodological framework for project-specific acceptance criteria, not a compliance claim or ready-made vehicle limits. Protocol and thresholds require the team and supervisor’s decision.'))}</p>
 </details>;
}

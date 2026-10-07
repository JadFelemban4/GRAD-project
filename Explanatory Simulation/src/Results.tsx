import { uiText } from './model/ui-copy.mjs';
import { useUI } from './useUI';
import { usePreferences } from './Preferences';
import { selectedPair, includesZero } from './model/provenance.mjs';
import { useEffect, useState } from 'react';
import { api, humanWarning } from './types';
import { Evidence } from './Inspector';

function ltr(value: string | number, className?: string) {
  return <bdi dir="ltr" className={className}>{value}</bdi>;
}

function findingArabic(text: string, language: "ar" | "en") {
  const ui = <T,>(value:T):T => uiText(value, language);

  if (text.startsWith('SPARK.')) {
    const a = text.match(/every agent advances spark ([\d.]+)-([\d.]+) deg past the baseline \(median; the trim's upper bound is \+([\d.]+)\), whose own spark there is ([\d.]+) deg\. That takes the modelled knock integral from the baseline's ([\d.]+) to ([\d.]+)-([\d.]+) \(95th percentile\), just under the ([\d.]+) knee/i);
    if (a) return <>{ui("على الصعود، يزيد كل وكيل توقيت الشرارة ")}<bdi dir="ltr">{ui(a[1])}–{ui(a[2])}°</bdi> {ui(" عن المرجع (الحد الأعلى للتعديل ")}<bdi dir="ltr">+{ui(a[3])}°</bdi>{ui("؛ وتوقيت المرجع هناك ")}<bdi dir="ltr">{ui(a[4])}°</bdi>{ui("). يرفع ذلك مؤشر الطرق المحاكى من ")}<bdi dir="ltr">{ui(a[5])}</bdi> {ui(" إلى ")}<bdi dir="ltr">{ui(a[6])}–{ui(a[7])}</bdi> {ui(" (المئين 95)، دون العتبة المفترضة ")}<bdi dir="ltr">{ui(a[8])}</bdi>{ui(". قد يفسر هذا جزءًا من مكسب الوكلاء على السياسات اليدوية، اعتمادًا على نموذج طرق غير متحقق منه. الاستباق لا يتأثر لأن السياستين المطلعة والعمياء تفعلان ذلك معًا.")}</>;
    return ui('يذكر التقرير أن تقديم الشرارة يفسر جزءًا من فارق الوكلاء، لكن هذا التفسير يعتمد على نموذج طرق غير متحقق منه.');
  }
  if (text.startsWith('BLIND_SEED6')) {
    const a = text.match(/on ([\d]+) of ([\d]+) episodes \(numbers ([^)]+); worst ([\d]+) against ([\d]+), peak turbine ([\d.]+) C\)/i);
    if (a) return <>{ui("سجّل الوكيل الأعمى seed6 ضررًا أعلى من وحدة التحكم الأساسية في ")}<bdi dir="ltr">{ui(a[1])} {ui(" من ")}{ui(a[2])}</bdi> {ui(" حلقة (أرقامها ")}<bdi dir="ltr">{ui(a[3])}</bdi>{ui("). أسوأ قيمة ")}<bdi dir="ltr">{ui(a[4])}</bdi> {ui(" مقابل ")}<bdi dir="ltr">{ui(a[5])}</bdi> {ui(" للمرجع، وبلغت حرارة التوربين ")}<bdi dir="ltr">{ui(a[6])}°C</bdi>{ui(". لذلك لا تضمن النتيجة الوسيطة حماية كل حلقة.")}</>;
    return ui('سجّل أحد الوكلاء ضررًا أعلى من وحدة التحكم الأساسية في بعض الحلقات؛ لذلك لا تضمن النتيجة الوسيطة حماية كل حلقة.');
  }
  if (text.startsWith('20 of 20 agents')) {
    const a = text.match(/(\d+) of (\d+) agents beat the best hand-written policy on median damage \(([\d.]+) % cut\)\. (\d+) burn less fuel/i);
    if (a) return <>{ui("تفوقت ")}<bdi dir="ltr">{ui(a[1])} {ui(" من ")}{ui(a[2])}</bdi> {ui(" وكيلًا على أفضل سياسة يدوية في وسيط خفض الضرر (")}<bdi dir="ltr">{ui(a[3])}%</bdi>{ui("). واستهلك ")}<bdi dir="ltr">{ui(a[4])}</bdi> {ui(" وكلاء وقودًا أقل من المرجع.")}</>;
    return ui('تفوقت الوكلاء في وسيط الضرر، بينما استهلك بعضهم وقودًا أقل من المرجع.');
  }
  return ui('ملاحظة واردة في التقرير المولد؛ افتح ملف النتيجة لقراءة النص الأصلي.');
}

const sourceLabels: Record<string, string> = {
  'results/agents/terrain_dt1/index.json': 'ملخص الوكلاء واختبار الاستباق ومصدر التدريب',
  'results/agents/terrain_dt1/README.md': 'جدول الاستئصال والفروق بين البذور',
  'results/agents/terrain_dt1/KNOCK_MARGIN.md': 'تشخيص تقييد تقديم الشرارة',
  'results/premise.json': 'نتائج السياسات اليدوية على النموذج الحالي',
};

export default function Results({ onSource, seed, onSeedChange: setSeed }: { onSource: (source: any) => void; seed: number; onSeedChange: (seed: number) => void }) {
  const { format, message, ui, uiTemplate } = useUI();

  const { t, direction, language } = usePreferences();
  const [data, setData] = useState<any>(); const [error, setError] = useState(''); const [thermal, setThermal] = useState(false);
  useEffect(() => { api('results').then(setData).catch(e => setError(e.message)); }, []);
  if (error) return <div className="error" dir={direction}>{message(error)}</div>;
  if (!data) return <p className="empty" dir={direction}>{ui("جارٍ قراءة ملفات النتائج الحالية…")}</p>;
  const index = data.index, a = index?.ablation;
  if (!index || !a) return <div className="error" dir={direction}>{ui("النتيجة البحثية الحالية غير متاحة. لن نستبدلها بأرقام تاريخية.")}</div>;
  if (data.verdict !== 'INCONCLUSIVE') return <div className="error" dir={direction}>{ui("تغيّرت النتيجة المقترنة وتحتاج إلى مراجعة قبل عرض هذا الاستنتاج التعليمي. افتح مصدر النتيجة الحالية.")}<button onClick={() => onSource({ file: 'results/agents/terrain_dt1/index.json', line: 1 })}>{ui("اقرأ ملف النتائج")}</button></div>;
  const diagnostic = String(data.knock_margin || '').split('\n').find(line => line.startsWith('- **Median cut'))?.replaceAll('**', '').replace(/^- /, '');
  const pairs = a.pairs || [];
  const chosen = selectedPair(index, seed);
  const list = Object.entries(index.policies || {}).map(([name, p]: [string, any]) => ({ name, value: p[thermal ? 'thermal_cut_pct' : 'cut_pct'], fuel: p.fuel_vs_baseline_pct, worst: p.damage?.worst }));
  return <div className="results-content" dir={direction}><span className="small-label">{ui("ماذا أظهرت التجربة؟")}</span><h2>{ui("تحسن وسيط الضرر مع الإشراف.")}<br/>{ui("وأثر الاستباق غير حاسم.")}</h2>
    <div className="result-verdict"><span className="badge unverified" dir={direction}>{ui("غير حاسم")}</span><strong>{ui(ltr(uiTemplate("{0} نقطة مئوية", "{0} percentage points", format(a.mean, 2))))}</strong><span>{ui("متوسط أفضلية الاستباق")}</span><p dir={direction}>{ui("فاصل الثقة 95%: ")}{ui(ltr(uiTemplate("{0} إلى {1} نقطة مئوية", "{0} to {1} percentage points", format(a.ci95?.[0], 2), format(a.ci95?.[1], 2))))} {ui(" عبر ")}{ui(ltr(a.n))} {ui(" أزواج من البذور. يشمل الفاصل الصفر وآثارًا قد تكون مهمة.")}</p></div>
    <div className="ci-plot"><svg viewBox="0 0 640 90" role="img" aria-label={ui("فاصل الثقة لأفضلية الاستباق")}><line x1="50" x2="600" y1="38" y2="38" stroke="#c6d1d4"/>{[-5, 0, 5, 10].map(v => <g key={v}><line x1={50 + (v + 10) / 25 * 550} x2={50 + (v + 10) / 25 * 550} y1="12" y2="58" stroke={v === 0 ? '#76888e' : '#dce4e6'} strokeDasharray="3 3"/><text x={50 + (v + 10) / 25 * 550} y="78" textAnchor="middle" fontSize="12">{ui(v)} pp</text></g>)}<line x1={50 + (a.ci95[0] + 10) / 25 * 550} x2={50 + (a.ci95[1] + 10) / 25 * 550} y1="38" y2="38" stroke="#127d87" strokeWidth="5"/><circle cx={50 + (a.mean + 10) / 25 * 550} cy="38" r="7" fill="#127d87"/></svg></div>
    <p className="subtle">{ui("مجموعة النتائج: ")}{ui(ltr(index.set))} {ui(" · تاريخ الإنشاء ")}{ui(ltr(index.generated))} · {ui(ltr(a.n * 2))} {ui(" وكيل SAC · ميزانية التدريب ")}{ui(ltr('50,000'))} {ui(" خطوة · تقييم التسلق المقفل عند ")}{ui(ltr('12% / 130 km/h'))}. {ui(index.regression_checked === 0 && 'يسجل التقرير صفر حلقات جرى فحص تراجعها.')}</p>
    <h3>{ui("اختلاف البذور أكبر من متوسط الأثر")}</h3><div className="pair-grid">{pairs.map((p: any) => { const v = p.sighted - p.blinded; return <div key={p.seed}><button aria-pressed={seed===p.seed} onClick={()=>setSeed(p.seed)} data-testid={`seed-pair-${p.seed}`}>{ui(t("اختر الزوج", "Select pair"))} {ui(ltr(p.seed))}</button><small>{ui("البذرة ")}{ui(ltr(p.seed))}</small><strong className={v >= 0 ? 'positive' : 'negative'} dir="ltr">{ui(v >= 0 ? '+' : '')}{ui(format(v, 1))} pp</strong><span>{ui(v >= 0 ? 'رجّح الاستباق' : 'تفوقت السياسة العمياء')}</span></div>; })}</div>
    <section className="notice" data-testid="selected-seed-pair"><h3>{ui(t('زوج التدريب المختار','Selected training pair'))} <bdi dir="ltr">{ui(seed)}</bdi></h3>
      {chosen ? <><p><code dir="ltr">sighted_seed{seed}</code>: {ui(ltr(format(chosen.pair.sighted,3)))}% · <code dir="ltr">blind_seed{seed}</code>: {ui(ltr(format(chosen.pair.blinded,3)))}%</p><p>{ui(t('خفض وسيط مؤشر الضرر عن ECU المرجعية؛ الفرق بين النسب','Median damage-proxy reduction relative to baseline ECU; difference between percentages'))}: {ui(ltr(format(chosen.delta,3)))} pp. {ui(t('النقطة المئوية ليست نسبة تغير جديدة.','A percentage point is not a new relative percent change.'))}</p>
      {[['sighted',chosen.sighted],['blind',chosen.blind]].map(([name,policy]:any)=><div key={name}><code dir="ltr">{name}_seed{seed}</code><p>{ui(t('تشخيص torque_viol المسجل (median / Q1 / Q3 / worst / best):','Recorded torque_viol diagnostic (median / Q1 / Q3 / worst / best):'))} <bdi dir="ltr">{ui(['median','q1','q3','worst','best'].map(k=>format(policy?.torque_viol?.[k],3)).join(' / '))}</bdi></p><p>{ui(t('إعداد النسخة المنتجة:','Producing-version config:'))} <code dir="ltr">{policy?.config?.git_commit ?? '—'} · git_dirty={String(policy?.config?.git_dirty ?? '—')}</code></p></div>)}</> : <p>{ui(t('الزوج غير متاح؛ لا نعوّضه بأرقام مصطنعة.','Pair unavailable; no manufactured values.'))}</p>}
      <p>{ui(t('التعريف في الشيفرة الحالية: torque_viol هو مجموع cost_torque عبر خطوات الحلقة، وليس نسبة مخالفات أو عددًا أو منحنى لكل خطوة. لا تؤكد هذه الشيفرة وحدها هوية النسخة المنتجة للملف التاريخي المتسخ.','Current-code definition: torque_viol is the episode sum of cost_torque, not a violation percentage, count or per-step curve. Current code alone does not verify the producing version of the dirty historical artifact.'))}</p>
      <p>{ui(t('بذرة التدريب تغيّر تهيئة الشبكة والاستكشاف وعينات التعلم؛ نفس الإعدادات لا تعني نفس الأوزان. هذا تفسير عام للتباين وليس إثباتًا لسبب فرق هذا الزوج. بذور التقييم 1000–1019 لعدد 20 حلقة مجمدة، 720 s وdt=1، صعود 12% / 130 km/h / 42°C وأوزان تكلفة ثابتة. في الجسر المقفل، بذرة الطريق 1000 وأوزان الحلقة المصدرية ثابتة؛ اختيار زوج التدريب لا يغيّر الطريق أو الطقس.','Training seed affects network initialization, exploration and learning samples; identical settings do not imply identical weights. This is a general explanation of variation, not a proven cause for this pair. Evaluation seeds 1000–1019 cover 20 frozen episodes, 720 s and dt=1, locked 12% / 130 km/h / 42°C climb and fixed cost weights. The locked bridge uses road seed 1000 and its source episode weights; selecting a training pair does not change road or weather.'))}</p>
      <p><code dir="ltr">predict(..., deterministic=True)</code> · {ui(t('إعادة تقييم السياسة نفسها لا تسحب فعلاً عشوائيًا كل مرة. إعادة تشغيل أوزان policy.npz المصدّرة ليست النتيجة التاريخية المطابقة لملفات final.zip.','Evaluating the same policy does not draw a random action each time. Replaying exported policy.npz weights is not the identical historical result scored with final.zip artifacts.'))}</p>
      <p>{ui(includesZero(a.ci95) ? t('فاصل المجموعة يشمل الصفر: النتيجة غير حاسمة، لا يثبت ذلك انعدام الأثر ولا التعميم لكل سيارة.','The group interval includes zero: inconclusive, not proof of no effect or generalization to every car.') : t('فاصل المجموعة يحتاج مراجعة.','Group interval requires review.'))}</p>
      <details><summary>{ui(t('سؤال مناقشة: كيف تفرق مكسبًا ثابتًا عن اختيار أفضل seed؟','Discussion: how do you distinguish a stable gain from choosing the best seed?'))}</summary><p>{ui(t('فسّر الزوج المختار ثم ارجع إلى كل الأزواج وفاصل المجموعة أعلاه؛ التدريب المتكرر يختلف عن إعادة تشغيل السياسة نفسها. الملاءمة تختلف عن اختبار مستقل، والمقارنة اليدوية predictive تجيب سؤالاً آخر.','Explain the selected pair, then return to all pairs and the group interval above. Repeated training differs from replaying one policy. Calibration differs from independent testing; the manual predictive comparison answers a different question.'))}</p></details>
      <div className="chain-links">{[{file:'results/agents/terrain_dt1/index.json',line:1},{file:'evaluate.py',line:134},{file:'engine_env.py',line:960},{file:'engine_env.py',line:969},{file:'evaluate.py',line:298},{file:'train.py',line:493},{file:'results/agents/terrain_dt1/sighted_seed0/eval_summary.json',line:3}].map(source=><button key={`${source.file}:${source.line}`} onClick={()=>onSource(source)}>{source.file.endsWith('eval_summary.json') && <span>{ui(t('مثال بروتوكول seed 0: ','Seed 0 protocol example: '))}</span>}<code dir="ltr">{source.file}:{source.line}</code></button>)}</div>
    </section>
    <div className="notice"><strong>{ui("السياسات المكتوبة يدويًا تجيب عن سؤال مختلف.")}</strong><p>{ui("في الفرضية الحالية، الفرق بين الحماية التنبؤية والحماية المعتمدة على الميل الحالي هو ")}{ui(ltr(uiTemplate("{0} نقطة مئوية", "{0} percentage points", format(data.premise?._preview_over_current_grade_pts, 2))))}{ui(". والفرق الأكبر عن سياسة الحرارة التفاعلية البحتة ")}{ui(ltr(uiTemplate("{0} نقطة مئوية", "{0} percentage points", format(data.premise?._preview_over_reactive_pts, 2))))}{ui(". يظل الميل الحالي متاحًا دون الاستباق.")}</p><button onClick={() => onSource({ file: 'results/premise.json', line: 1 })}>{ui("افتح مصدر الفرضية")}</button></div>
    <div className="section-head"><h3>{ui("اعرض المقارنات كلٌّ على حدة")}</h3><button className="text-button" onClick={() => setThermal(!thermal)}>{ui(thermal ? 'اعرض الضرر الكلي' : 'اعرض الضرر الحراري فقط')}</button></div>
    <div className="result-bars">{list.map(p => <div className="result-row" key={p.name}><span dir="ltr">{ui(p.name)}</span><div><svg viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2={Math.max(0, p.value || 0)} y1="5" y2="5" stroke={p.name.includes('seed') ? '#127d87' : '#738c92'} strokeWidth="5"/></svg></div><strong dir="ltr">{ui(format(p.value))}%</strong><small>{ui("الوقود ")}{ui(p.fuel > 0 ? '+' : '')}{ui(format(p.fuel))}%</small></div>)}</div>
    <div className="notice"><strong>{ui("الضرر مؤشر تقريبي، وليس عمر مكونات مقاسًا.")}</strong><p>{ui("يعتمد مكسب وسيط السياسات المتعلمة بدرجة كبيرة على تقديم الشرارة قرب عتبة الطرق غير المتحقق منها.")}</p><p>{ui(diagnostic ? findingArabic(diagnostic, language) : 'تشخيص تقييد الشرارة غير متاح.')}</p><p>{ui("لم تُدرّب الوكلاء مع هذا القيد؛ لذا فهذا تشخيص خارج توزيع التدريب. وقد يخفي الوسيط حلقات ضارة.")}</p><button onClick={() => onSource({ file: 'results/agents/terrain_dt1/KNOCK_MARGIN.md', line: 3 })}>{ui("افتح تشخيص هامش الطرق")}</button></div>
    <details><summary>{ui("ما الذي رصده التقرير المولد؟")}</summary>{index.findings?.map((f: string, i: number) => <p key={i}>{ui(findingArabic(f, language))}</p>)}</details>
    {(data.caveats || []).map((c: any, i: number) => <p className="subtle" key={i}>{ui(humanWarning(typeof c === 'string' ? c : JSON.stringify(c)))}</p>)}
    <details><summary>{ui("التفاصيل الإحصائية ومصادر البيانات")}</summary><p>{ui("قيمة اختبار t هي ")}{ui(ltr(format(a.p_t, 4)))}{ui("؛ وقيمة اختبار Wilcoxon هي ")}{ui(ltr(format(a.p_wilcoxon, 4)))}{ui(". وهما يختلفان عن معيار MEI المسجل مسبقًا بوحدات الضرر. متوسط أثر الاستباق الحراري فقط: ")}{ui(ltr(uiTemplate("{0} نقطة مئوية", "{0} percentage points", format(a.thermal_mean, 2))))}.</p><div className="chain-links">{data.sources?.map((s: any) => <button key={s.file} onClick={() => onSource(s)}>{ui(sourceLabels[s.file] || 'افتح المصدر')}</button>)}</div><p>{ui("تنتمي تجارب Phase D وD2 وC4 الأقدم إلى نموذج سابق؛ ولا تدخل في هذه النتيجة الرئيسة.")}</p><pre dir="ltr">{JSON.stringify(data.freshness, null, 2)}</pre></details>
  </div>;
}

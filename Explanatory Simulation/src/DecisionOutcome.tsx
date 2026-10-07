import { useUI } from './useUI';
import {usePreferences} from './Preferences';
import {format} from './types';
import type {ReadingContext} from './types';
import type {ProjectStoryData} from './model/project-story.mjs';
import {decisionOutcome} from './model/decision-evaluation.mjs';
export default function DecisionOutcome({frame,story,sessionId,onSelect,sourceOnly=false}:{frame:any;sourceOnly?:boolean;story:ProjectStoryData;sessionId:string;onSelect:(id:string,reading?:ReadingContext)=>void}) {
  const { format, ui } = useUI();

 const {t,direction}=usePreferences(); const o=decisionOutcome(frame,story);
 const show=(v:number|null,digits=3)=>v===null?t('غير متاح','Unavailable'):format(v,digits);
 const rows:[string,string,string,string,string,number|null,number|null,ReadingContext['phase']][]=[
 ['torque_req',t('طلب الفترة','Interval torque demand'),'Nm','outputs.torque_req','torque_req',o.demand,null,'interval'],
 ['torque',t('العزم المتحقق / المرجع','Delivered / reference torque'),'Nm','outputs.torque','engine_torque',o.torque,o.baselineTorque,'interval'],
 ['error',t('خطأ التتبع: المتحقق − الطلب','Tracking error: delivered − demand'),'Nm','torqueErrorNm','r_resp',o.errorNm,null,'interval'],
 ['fuel',t('تدفق الوقود / المرجع','Fuel flow / reference'),'g/s','outputs.mdot_fuel','fuel',o.fuel,o.baselineFuel,'interval'],
 ['damage',t('معدل مؤشر الضرر / المرجع','Damage index rate / reference'),'index/s','damageRate','damage',o.damageRate,o.baselineDamageRate,'end'],
 ];
 const select=(id:string,field:string,phase:ReadingContext['phase'],label:string,unit:string)=>onSelect(id,{conceptId:id,field,phase,label,unit,digits:4,sessionId});
 return <section className="decision-outcome" data-testid="decision-outcome" data-session-id={sessionId} dir={direction}>
 <h3>{ui(t('هل حقق القرار هدفه؟','Did the decision meet its objective?'))}</h3>
 <p>{ui(t('العينة المختارة الحالية','Current selected sample'))} · <bdi dir="ltr">{ui(show(story.timeline.inputS,1))}–{ui(show(story.timeline.endS,1))} s</bdi></p>
 {sourceOnly&&<p>{ui(t('أزرار هذه البطاقة تفتح المصدر فقط؛ القراءات المعروضة تخص جلسة هذا المسار ولا تُرسل إلى مفتش المسار الآخر.','Buttons in this card open source only; displayed readings belong to this lane session and are not sent to the other lane Inspector.'))}</p>}
 <dl>{rows.map(([key,label,unit,field,id,value,reference,phase])=><div key={key}><dt><button type="button" onClick={()=>select(id,field,phase,label,unit)}>{ui(label)}{sourceOnly&&<> · {ui(t('افحص المصدر','Inspect source'))}</>}</button></dt><dd dir="ltr">{ui(show(value))} {ui(unit)}{['torque','fuel','damage'].includes(key)&&<> / {ui(show(reference))} {ui(unit)}</>}</dd></div>)}</dl>
 <p>{ui(t('خطأ نسبي ومقامه طلب الفترة','Relative error; denominator is interval demand'))}: <bdi dir="ltr">{ui(show(o.errorPct))}% / {ui(show(o.demand))} Nm</bdi></p>
 <p>{ui(t('تكامل هذه الفترة = المعدل × زمن الخطوة','This interval integral = rate × step duration'))}: <bdi dir="ltr">{ui(show(o.intervalDamage,5))} index</bdi></p>
 <p>{ui(t('تراكم الضرر / المرجع منذ بداية الجلسة','Cumulative damage / reference since session start'))}: <bdi dir="ltr">{ui(show(o.totalDamage,5))} / {ui(show(o.baselineTotalDamage,5))} index</bdi></p>
 <p>{ui(t('تراكم الوقود / المرجع','Cumulative fuel / reference'))}: <bdi dir="ltr">{ui(show(o.totalFuel))} / {ui(show(o.baselineTotalFuel))} g</bdi></p>
 <p>{ui(t('خفض تدفق الوقود؛ مقامه تدفق المرجع','Fuel flow reduction; denominator is reference flow'))}: <bdi dir="ltr">{ui(show(o.fuelReductionPct))}% / {ui(show(o.baselineFuel))} g/s</bdi></p>
 <p>{ui(t('خفض تراكم الضرر؛ مقامه تراكم المرجع','Cumulative damage reduction; denominator is reference total'))}: <bdi dir="ltr">{ui(show(o.damageReductionPct))}% / {ui(show(o.baselineTotalDamage,5))} index</bdi></p>
 <p>{ui(t('الصفر والسالب نتائج فعلية. لا يُحسب خفض بمقام مفقود أو غير موجب. انخفاض الوقود أو الضرر يُقرأ بجوار تلبية طلب العزم؛ قد لا يتحسن هذا المثال، ولا يثبت أمثلية عالمية.','Zero and negative values are actual results. A missing or nonpositive denominator prevents a reduction calculation. Read fuel and damage alongside torque delivery; this example may show no improvement and does not prove global optimality.'))}</p>
 <details data-testid="reward-accounting"><summary>{ui(t('كيف حسبنا التقييم؟','How was the evaluation computed?'))}</summary>
 <div className="decision-paths">{[['r_resp','العزم → استجابة العزم','Torque → torque response'],['r_fuel','الوقود → جزء الوقود','Fuel → fuel term'],['r_life','حرارة / طرق → معدل الضرر → جزء الضرر','Temperature / knock → damage rate → life term']].map(([id,ar,en],i)=><button type="button" key={id} onClick={()=>select(id,`rewardFields.${id}`,'end',t(ar,en),'')}>{ui(t(ar,en))}{sourceOnly&&<> · {ui(t('افحص المصدر','Inspect source'))}</>} <code dir="ltr">{id}</code> <bdi dir="ltr">{ui(show(o.terms[i],4))} × {ui(show(o.weights[i],4))}</bdi></button>)}</div>
 <code className="equation" dir="ltr">r_resp = −(e + 25·max(0,e−0.05)); e = |demand−torque| / max(demand,40 Nm)<br/>r_fuel = (reference fuel−fuel) / (reference fuel+1e−6)<br/>r_life = (reference rate−rate) / (reference rate+0.05)</code>
 <p>{ui(t('الأوزان المستخدمة فعلًا من ملاحظة الدخل','Actual weights from input observation'))} <code dir="ltr">obs_in[20:23]</code>: <bdi dir="ltr">{ui(o.weights.map(v=>show(v,4)).join(' / '))}</bdi></p>
 <code className="equation" dir="ltr">reward = w[0]·r_resp + w[1]·r_fuel + w[2]·r_life − uncertainty penalty − smoothness penalty</code>
 <p>{ui(o.complete?t('تفصيل مكتمل','Complete decomposition'):t('تفصيل جزئي: عقوبتا عدم اليقين والنعومة غير مُصدّرتين','Partial decomposition: uncertainty and smoothness penalties are not exported'))}</p>
 <p>{ui(t('المجموع الموزون المتاح','Available weighted subtotal'))}: <bdi dir="ltr">{ui(show(o.weightedSubtotal,4))}</bdi> · {ui(t('عقوبة عدم اليقين / النعومة','Uncertainty / smoothness penalty'))}: <bdi dir="ltr">{ui(show(o.uncertainty,4))} / {ui(show(o.smoothness,4))}</bdi></p>
 <button type="button" onClick={()=>select('policy_reward','reward','end',t('المكافأة الكلية المصدّرة','Exported total reward'),'')}>{ui(t('المجموع هو مكافأة المصدر','Total is source reward'))}{sourceOnly&&<> · {ui(t('افحص المصدر','Inspect source'))}</>} <code dir="ltr">frame.reward</code>: <bdi dir="ltr">{ui(show(o.reward,4))}</bdi></button>
 <p>{ui(t('تكاليف العزم والطرق وEGT تشخيصات؛ لا تُخصم مرة ثانية. المكافأة تصميم من مقادير البيئة والمرجع وتفضيلات الهدف، وليست label لأفضل فعل ولا حساسًا مستقلًا للتحقق.','Torque, knock and EGT costs are diagnostics; do not subtract them again. Reward is designed from environment quantities, reference and objective preferences; it is neither a label for the best action nor an independent validation sensor.'))}</p>
 <p>{ui(t('معدل الضرر يجمع أسّيات حرارة التوربين والزيت وحد الطرق الاختياري. المؤشر نسبي/ثانية؛ تراكمه مجموع المعدل × dt. خفض 12% لا يعني زيادة العمر 12%، وفرق نقطتين مئويتين ليس نسبة خفض جديدة.','Damage rate combines exponential turbine and oil temperatures with optional knock. It is a relative index per second; accumulation sums rate × dt. A 12% reduction does not mean 12% longer life; a difference in percentage points is not a new reduction percentage.'))}</p>
 <button type="button" onClick={()=>onSelect('damage')}>{ui(t('افحص مصدر معدل الضرر','Inspect damage rate source'))} <code dir="ltr">engine_env.py:636</code></button><button type="button" onClick={()=>onSelect('policy_reward')}>{ui(t('افحص مصدر المكافأة','Inspect reward source'))} <code dir="ltr">engine_env.py:934–946</code></button>
 </details>
 </section>;
}

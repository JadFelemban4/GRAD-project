import { useUI } from './useUI';
import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Eye, EyeOff, Gauge, Thermometer, Waves } from 'lucide-react';
import { format } from './types';
import type { Road, Meta, ReadingContext } from './types';
import {usePreferences} from './Preferences';
import ControllerRoles from './ControllerRoles';
import DecisionOutcome from './DecisionOutcome';
import {roleFor} from './model/decision-evaluation.mjs';
import type {ControllerRole} from './model/decision-evaluation.mjs';
import ActuatorEditor from './ActuatorEditor';
import { commandChains, commandReadings } from './model/supervisor.mjs';
import { buildProjectStory } from './model/project-story.mjs';

type Props = {
  actions: Meta['actions'];
  draft: number[];
  onDraftChange: (next:number[])=>void;
  activePolicy: string;
  comparison: boolean;
  frame: any;
  previousFrame?: any;
  sessionId: string;
  resetKey: string;
  observations?: Meta['observations'];
  preview: boolean;
  road?: Road;
  time: number;
  onSelect: (concept: string, reading?: ReadingContext) => void;
  onPreviewChange?: (preview: boolean) => void;
  onAdvance?: () => void;
  onExample?: () => void;
  busy: boolean;
  policyLabel: string;
};

function reading(value: number | null, digits = 1) {
  return value === null ? 'غير متاح' : format(value, digits);
}

export default function ProjectStory({ frame, preview, road, time, onSelect, onPreviewChange, onAdvance, onExample, busy, policyLabel, previousFrame, sessionId, resetKey, observations, actions, draft, onDraftChange, activePolicy, comparison }: Props) {
  const { ui, uiTemplate, format } = useUI();
  const reading = (value: number | null, digits = 1) => format(value, digits);

  const {t,direction}=usePreferences();
  const [role,setRole]=useState<ControllerRole>('policy');
  const [stage, setStage] = useState(0);
  const [actuator, setActuator] = useState(0);
  const action=actions[actuator];
  const exportedChain=commandChains(frame)[actuator];
  const chain={...exportedChain,unit:action?.unit || exportedChain.unit,finalUnit:actuator===2?"kPa abs":actuator===0?"°BTDC":action?.unit || exportedChain.finalUnit};
  useEffect(()=>setStage(0),[resetKey]);
  const story = buildProjectStory(frame, { preview, road, time, previousFrame, sessionId, previousSessionId:sessionId });
  const selectReading = (conceptId: string, field: string, phase: ReadingContext['phase'], label: string, unit: string, digits = 1) => {setRole(roleFor(conceptId));onSelect(conceptId, {conceptId, field, phase, label, unit, digits, sessionId});};
  const rewardLabels: Record<string,string> = {r_resp:'جزء استجابة العزم',r_fuel:'جزء الوقود',r_life:'جزء الحفاظ على المكونات',cost_torque:'تكلفة عجز العزم',cost_knock:'تكلفة الطرق',cost_egt:'تكلفة حرارة العادم'};
  const titles=['الطريق','ما قرأه','الأمر','النتيجة','القرار التالي'];
  const horizons = ['preview_2s', 'preview_5s', 'preview_15s', 'preview_30s'];
  return <section className="project-story" aria-label={ui("حلقة قرار المشرف في خمس مراحل")} dir={direction}>
    <header className="project-story__header">
      <span className="project-story__eyebrow">{t('تجربة تعليمية · حلقة واحدة من الجلسة الحالية', 'Teaching experiment · one loop from the current session')}</span>
      <h2>{t('كيف نفهم قرار المشرف؟', 'How do we understand the supervisor decision?')}</h2>
      <p>{ui("يقرأ الطريق والطلب، ويطبّق أمرًا، ثم نرى ما نتج خلال الخطوة وما بقي في نهايتها.")}</p>
      <div className="project-story__timeline" aria-label={ui("توقيت القرار والنتيجة")}><span>{ui("دخل القرار ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))} s</bdi></span><ArrowLeft size={13}/><span>{ui(story.timeline.hasAppliedAction?'حساب الفترة':'قبل التنفيذ')} <bdi dir="ltr">{ui(story.timeline.hasAppliedAction?`${format(story.timeline.inputS,0)}–${format(story.timeline.endS,0)} s`:'—')}</bdi></span><ArrowLeft size={13}/><span>{ui(story.timeline.hasAppliedAction?'حرارة النهاية':'حالة البداية')} <bdi dir="ltr">{ui(format(story.timeline.endS,0))} s</bdi></span></div>
      {onExample && <button className="project-story__example" disabled={busy} onClick={onExample}>{ui("شاهد مثالًا قبل الصعود")}</button>}
    </header>

    <ControllerRoles story={story} frame={frame} stage={stage} sessionId={sessionId} onStage={setStage} onSelect={onSelect} selected={role} onRole={setRole}/>
    <nav className="project-story__stages" aria-label={ui("مراحل حلقة القرار")}>{titles.map((title,index)=><button key={title} type="button" aria-current={stage===index?'step':undefined} onClick={()=>setStage(index)}><span>{ui(index+1)}</span>{ui(title)}</button>)}</nav>
    <p className="project-story__loop" dir={direction}>{ui("ما قرأه المشرف ← الأمر ← النتيجة ← الحالة الجديدة")}</p>
    {stage === 0 && <article className="project-story__step">
      <div className="project-story__step-head"><span className="project-story__number">01</span><div><h3>{ui("يرى الطريق القادم")}</h3><p>{ui("الميل الحالي يبقى معلومًا حتى عند حجب المعاينة المستقبلية.")}</p></div><Waves size={18}/></div>
      <div className="project-story__current"><span>{ui("الميل عند دخل القرار ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))} s</bdi></span><button type="button" onClick={() => selectReading('grade','currentGradePct','input','الميل عند دخل القرار','%')}><bdi dir="ltr">{ui(reading(story.currentGradePct))}%</bdi></button></div>
      <div className="project-story__preview" aria-label={ui("درجات الطريق عند آفاق المعاينة")}>
        {story.previewSlots.map((slot, index) => <button className="project-story__horizon" type="button" key={slot.seconds} onClick={() => selectReading(horizons[index],`previewSlots.${index}`,'input',uiTemplate("ميل الطريق بعد {0} ثانية", "Road grade after {0} seconds", slot.seconds),'%')} aria-label={ui(uiTemplate("ميل الطريق بعد {0} ثانية", "Road grade after {0} seconds", slot.seconds))}>
          <small dir="ltr">+{ui(slot.seconds)} s</small><strong dir="ltr"><bdi>{ui(reading(slot.gradePct))}%</bdi></strong>
        </button>)}
      </div>
      <p className="project-story__note">{ui("هذه معاينة من مسار التجربة، وليست قراءة كاميرا أو حساس طريق.")}</p>
      {onPreviewChange && <button type="button" className="project-story__preview-toggle" aria-pressed={preview} disabled={busy} onClick={() => onPreviewChange(!preview)}>
        {preview ? <Eye size={15}/> : <EyeOff size={15}/>} {ui(preview ? 'حجب معاينة المستقبل' : 'إظهار معاينة المستقبل')}
      </button>}
    </article>}



    {stage === 1 && <article className="project-story__step">
      <div className="project-story__step-head"><span className="project-story__number">02</span><div><h3>{ui("ماذا قرأت السياسة؟")}</h3><p>{ui("ملاحظة الدخل أنتجت الأمر. طلبها مخزّن من الخطوة السابقة؛ طلب الفترة يُحسب بعد اختيار الأمر.")}</p></div><Gauge size={18}/></div>
      <div className="project-story__readings">
        <button type="button" onClick={() => selectReading('torque_req','observedTorqueReqNm','input','طلب العزم الذي رأته السياسة','Nm')}><span>{ui("طلب العزم الذي رأته السياسة")}</span><strong dir="ltr"><bdi>{ui(reading(story.observedTorqueReqNm))}</bdi> <small>Nm</small></strong></button>
      </div>
      <p className="project-story__note">{ui("حرارة الدخل من نهاية العينة السابقة المطابقة؛ لا نستعمل حرارة نهاية الفترة كأنها كانت متاحة قبل الأمر.")}</p>
      <div className="project-story__readings">{story.memory.map(m=><button type="button" key={m.id} onClick={()=>selectReading(m.id,`memory.${m.id}.beforeC`,'input',uiTemplate("{0} عند الدخل", "{0} at input", m.label),'°C')}><span>{ui(m.label)} {ui(" عند الدخل")}</span><strong dir="ltr">{ui(reading(m.beforeC))} °C</strong></button>)}</div>
    </article>}
    {stage === 2 && <article className="project-story__step">
      <div className="project-story__step-head"><span className="project-story__number">03</span><div><h3>{ui("يعدّل فوق وحدة ECU")}</h3><p>{ui("ثلاثة تعديلات على خرج ECU؛ المروحة والمضخة أوامر تشغيل مطلقة.")}</p></div><Gauge size={18}/></div>
      <button type="button" className="project-story__policy" onClick={() => {setRole('policy');onSelect(frame?.mode==='trained_actor'?'agent':'policy_action');}}><span>{ui("وحدة التحكم الحالية")}</span><strong>{ui(policyLabel || 'غير متاح')}</strong></button>
      <div className="project-story__actuators" aria-label={ui("اختر مشغلًا")}>{story.controls.map((control,index)=><button type="button" key={control.id} aria-pressed={actuator===index} onClick={()=>{setActuator(index);setRole('policy');}}>{ui(control.label)}</button>)}</div>
      <div className="project-story__readings command-chain">
        {commandReadings(chain, sessionId).map(descriptor => (
          <button type="button" key={descriptor.key} onClick={() => {setRole('policy');onSelect(descriptor.conceptId, descriptor);}}>
            <span>{ui(descriptor.label)}</span>
            <strong dir="ltr">{ui(reading(chain[descriptor.key], descriptor.digits))} <small>{ui(descriptor.unit)}</small></strong>
          </button>
        ))}
      </div>
      <p className="project-story__note">{ui("دخل القرار ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))} s</bdi> {ui(" · النتيجة خلال ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))}–{ui(format(story.timeline.endS,0))} s</bdi>{ui(". حد التغيير ")}<bdi dir="ltr">{ui(format(action?.slew,2))} {ui(action?.slew_unit)}</bdi>{ui("، وزمن الخطوة ")}<bdi dir="ltr">{ui(reading(chain.dt,2))} s</bdi>{ui(". قد يختلف الطلب عن المطبّق بسبب حد التغيير وحدود المشغل ")}<bdi dir="ltr">{ui(action?.lo)}…{ui(action?.hi)} {ui(action?.unit)}</bdi>.</p>
      <p className="project-story__note">{ui(actuator===2?'ضغط المانيفولد ناتج حلقة PI لتتبّع العزم مع تعديل الضغط؛ المرجع حلقة موازية، وليس المرجع + التعديل.':actuator>=3?'المروحة والمضخة أوامر مطلقة؛ مرجع المروحة للمقارنة فقط، ومرجع المضخة غير مُصدّر.':'تعديل المشرف يضاف إلى مرجع ECU، ثم تُطبّق حدود المصدر؛ القيمة النهائية المعروضة مُصدّرة من المحاكاة.')}</p>
      <ActuatorEditor actions={actions} draft={draft} onChange={onDraftChange} activePolicy={activePolicy} comparison={comparison} busy={busy}/>
    </article>}



    {stage === 3 && <article className="project-story__step">
      <DecisionOutcome frame={frame} story={story} sessionId={sessionId} onSelect={(id,reading)=>{setRole(roleFor(id));onSelect(id,reading);}}/>
      <div className="project-story__step-head"><span className="project-story__number">04</span><div><h3>{ui("ماذا نتج؟")}</h3><p>{ui("مخرجات الفترة ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))}–{ui(format(story.timeline.endS,0))} s</bdi> {ui(" محسوبة بالنموذج.")}</p></div><Thermometer size={18}/></div>
      <div className="project-story__readings">{[['torque_req','طلب الفترة','Nm','torque_req'],['torque','العزم المتحقق','Nm','engine_torque'],['mdot_fuel','تدفق الوقود','g/s','fuel'],['mdot_air','تدفق الهواء','g/s','air'],['egt_c','غاز العادم خلال الفترة','°C','egt']].map(([id,label,unit,concept])=><button type="button" key={id} onClick={()=>selectReading(concept,`outputs.${id}`,'interval',label,unit)}><span>{ui(label)}</span><strong dir="ltr">{ui(reading(story.outputs[id]))} <small>{ui(unit)}</small></strong></button>)}</div>
      <p className="project-story__note">{ui("طلب الفترة ليس بالضرورة الطلب الذي رأته السياسة. عند البداية تبقى النتائج غير متاحة حتى تنفيذ أمر.")}</p>
    </article>}
    {stage === 4 && <article className="project-story__step">
      <div className="project-story__step-head"><span className="project-story__number">05</span><div><h3>{ui("ماذا بقي للقرار التالي؟")}</h3><p>{ui("الحالة عند ")}<bdi dir="ltr">{ui(format(story.timeline.endS,0))} s</bdi> {ui(" تدخل الملاحظة التالية.")}</p></div><Thermometer size={18}/></div>
      <div className="project-story__readings">{story.memory.map(m=><button type="button" key={m.id} onClick={()=>selectReading(m.id,`memory.${m.id}.afterC`,'end',uiTemplate("{0} عند النهاية", "{0} at end", m.label),'°C',2)}><span>{ui(m.label)}<small> {ui(" الدخل ← النهاية · الفرق")}</small></span><strong dir="ltr">{ui(reading(m.beforeC,2))} → {ui(reading(m.afterC,2))} °C<small> Δ {ui(reading(m.deltaC,2))} °C</small></strong></button>)}</div>
      {!story.previousMatches && <p className="project-story__note">{ui("لا توجد عينة سابقة مطابقة من هذه الجلسة؛ حرارة الدخل والفرق غير متاحين.")}</p>}
      <div className="project-story__readings"><button type="button" onClick={()=>selectReading('damage','damageRate','end','معدل الضرر عند النهاية','',5)}><span>{ui("معدل الضرر عند النهاية")}</span><strong dir="ltr">{ui(reading(story.damageRate,5))}</strong></button><div className="project-story__cumulative"><span>{ui("الضرر المتراكم في الجلسة")}</span><strong dir="ltr">{ui(reading(story.totalDamage,5))}</strong><small>{ui("مجموع مؤشر الضرر المتكامل منذ بداية الجلسة، وليس معدل هذه اللحظة.")}</small></div></div>
      <p className="project-story__note">{ui("الضرر مؤشر تقريبي؛ لا يتنبأ بالعمر الفعلي للمكونات.")}</p>
      <details className="project-story__detail"><summary>{ui("الملاحظة والمكافأة بالتفصيل")}</summary><p>{ui("نعيد تشغيل سياسة جاهزة. عرض المكافأة لا يعني تدريبًا مباشرًا؛ لا تتغير أوزان السياسة أثناء هذا التشغيل.")}</p><button type="button" onClick={()=>selectReading('policy_reward','reward','end','مكافأة الانتقال','',3)}>{ui("مكافأة الانتقال: ")}<bdi dir="ltr">{ui(reading(story.reward,3))}</bdi></button><dl>{Object.entries(story.rewardFields).map(([id,value])=><div key={id}><dt><button type="button" onClick={()=>selectReading(id.startsWith('cost_')?'constraint_costs':id,`rewardFields.${id}`,'end',rewardLabels[id],'',4)}>{ui(rewardLabels[id])} <small dir="ltr">{ui(id)}</small></button></dt><dd dir="ltr">{ui(reading(value,4))}</dd></div>)}</dl><p>{ui("قيم الملاحظة مطبّعة كما يعيدها المصدر؛ obs_in قبل الأمر، وobs بعده. لا تُجمع هذه الحقول يدويًا لصنع مكافأة جديدة.")}</p><p>{ui("الدخل ")}<bdi dir="ltr">{ui(format(story.timeline.inputS,0))} s</bdi> {ui(" ← ملاحظة القرار التالي ")}<bdi dir="ltr">{ui(format(story.timeline.endS,0))} s</bdi></p><div className="project-story__obs">{observations?.map((o,index)=><div key={index}><span>{ui(o.name || o.label || o.id || 'خانة')} <small dir="ltr">[{ui(index)}]</small><small className="project-story__scale" dir="ltr">{ui(o.scale)}</small></span><bdi dir="ltr">{ui(format(frame?.obs_in?.[index],3))} → {ui(format(frame?.obs?.[index],3))}</bdi></div>)}</div></details>
    </article>}

    <div className="project-story__navigation"><button type="button" disabled={stage===0} onClick={()=>setStage(stage-1)}>{ui("السابق")}</button><span>{ui(stage+1)} / 5</span><button type="button" disabled={stage===4} onClick={()=>setStage(stage+1)}>{ui("التالي")}</button></div>
    {onAdvance && <button type="button" className="project-story__advance" disabled={busy} onClick={onAdvance}>{ui(busy ? 'جارٍ تحديث الخطوة…' : 'نفّذ الخطوة التالية')}<ArrowRight size={16}/></button>}
  </section>;
}

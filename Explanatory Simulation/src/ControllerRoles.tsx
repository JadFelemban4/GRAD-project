import { useUI } from './useUI';
import {useEffect,useState} from 'react';
import {usePreferences} from './Preferences';
import type {ProjectStoryData} from './model/project-story.mjs';
import {roleSequence} from './model/decision-evaluation.mjs';
import type {ControllerRole} from './model/decision-evaluation.mjs';
export default function ControllerRoles({story,frame,stage,sessionId,onStage,onSelect,selected,onRole}:{story:ProjectStoryData;frame:any;stage:number;sessionId:string;onStage:(s:number)=>void;onSelect:(id:string)=>void;selected:ControllerRole;onRole:(r:ControllerRole)=>void}) {
  const { ui } = useUI();

 const {t,direction}=usePreferences();const [pulse,setPulse]=useState<ControllerRole|null>(null);
 useEffect(()=>{const sequence=roleSequence(story);const timers=sequence.map((r,i)=>setTimeout(()=>setPulse(r),i*350));timers.push(setTimeout(()=>setPulse(null),sequence.length*350));return ()=>timers.forEach(clearTimeout);},[sessionId,story.timeline.inputS,story.timeline.endS]);
 const roles:{id:ControllerRole;ar:string;en:string;stage:number;concept:string;arDetail:string;enDetail:string}[]=[
 {id:'policy',ar:'وحدة التحكم / خمسة أفعال',en:'Controller / five actions',stage:2,concept:frame?.mode==='trained_actor'?'agent':'policy_action',arDetail:'يقرأ obs_in ويختار تعديل الشرارة ولامدا والضغط وأمري المروحة والمضخة. SAC يختار الأفعال ولا يحسب حرارة المعدن.',enDetail:'Reads obs_in and chooses spark, lambda and pressure trims plus fan and pump commands. SAC chooses actions; it does not compute metal temperature.'},
 {id:'ecu',ar:'ECU / الحدود / PI',en:'ECU / limits / PI',stage:2,concept:'boost_trim',arDetail:'قيم ECU الأساسية وحدود التغيير والمشغلات، وحلقة PI لتتبع العزم، تحول طلب المشرف إلى القيم النهائية.',enDetail:'ECU baselines, slew and actuator limits, and torque-tracking PI turn supervisor requests into final inputs.'},
 {id:'engine',ar:'نموذج المحرك',en:'Engine model',stage:3,concept:'engine_torque',arDetail:'يحسب العزم والوقود وتدفق الهواء وحرارة غاز العادم خلال الفترة من المدخلات النهائية.',enDetail:'Computes interval torque, fuel, airflow and exhaust gas temperature from final inputs.'},
 {id:'thermal',ar:'الشبكة الحرارية',en:'Thermal network',stage:4,concept:'t_turb',arDetail:'تتكامل حالة معدن المحرك والزيت وحاوية التوربين؛ حرارة الغاز ليست حرارة المعدن.',enDetail:'Integrates engine metal, oil and turbine housing state; gas temperature is not metal temperature.'},
 {id:'reward',ar:'التقييم / الملاحظة التالية',en:'Evaluation / next observation',stage:4,concept:'policy_reward',arDetail:'البيئة تجمع مقاديرها والمرجع وأوزان الأهداف للمكافأة ثم تعيد obs للحالة التالية.',enDetail:'The environment combines its quantities, reference and objective weights into reward and returns obs for the next state.'},
 ];
 const current=roles.find(r=>r.id===selected)!;
 return <section className="controller-roles" data-testid="controller-roles" dir={direction}>
 <h3>{ui(t('من يحسب هذا؟','Who computes this?'))}</h3>
 <p>{ui(t('نتتبّع مسؤولية كل جزء في حساب العينة المختارة. قد تتكرر حلقة PI؛ ويُحسب المرجع في مسار موازٍ.','Follow each part’s responsibility in computing the selected sample. PI may repeat, and the reference is computed in a parallel path.'))} <bdi dir="ltr">{ui(story.timeline.inputS)}→{ui(story.timeline.endS)} s</bdi></p>
 <div className="controller-roles__blocks">{roles.map(r=><button type="button" key={r.id} data-role={r.id} data-pulse={pulse===r.id} aria-pressed={selected===r.id} aria-current={stage===r.stage?'step':undefined} onClick={()=>{onRole(r.id);onStage(r.stage);}}>{ui(t(r.ar,r.en))}</button>)}</div>
 <p>{ui(t(current.arDetail,current.enDetail))}</p><button type="button" onClick={()=>onSelect(current.concept)}>{ui(t('افحص مصدر هذه المسؤولية','Inspect this responsibility in source'))}</button>
 <p>{ui(frame?.mode==='trained_actor'?t('التشغيل الحالي يعيد استعمال أوزان SAC جاهزة ومجمّدة. التدريب مسار منفصل يحدّث أوزان السياسة من الانتقالات والمكافأة؛ لا يوجد تدريب حي هنا.','This run reuses frozen SAC weights. Training separately updates policy weights from transitions and reward; no live training occurs here.'):frame?.mode==='manual'?t('الوحدة الحالية أوامر يدوية؛ المسودة ليست خرج SAC متعلمًا.','The current controller uses manual commands; the draft is not a learned SAC output.'):t('الوحدة الحالية سياسة مكتوبة يدويًا، وليست وكيل SAC متعلمًا.','The current controller is a hand-written policy, not a learned SAC agent.'))}</p>
 <p>{ui(t('مسار التدريب منفصل: يحدث أوزان SAC من الانتقالات والمكافأة. إعادة التشغيل تستخدم أوزان جاهزة ولا تدربها.','Training is a separate path: it updates SAC weights from transitions and reward. Replay uses prepared weights without training them.'))} <button type="button" onClick={()=>onSelect('agent')}>{ui(t('مصدر التدريب','Training source'))} <code dir="ltr">train.py · SAC</code></button></p>
 <details><summary>{ui(t('لماذا RL بدل توقع الحرارة فقط؟','Why RL rather than only forecasting temperature?'))}</summary><p>{ui(t('هذه قرارات متتابعة يتغير أثرها مع الحالة والذاكرة الحرارية والمكافأة المتراكمة. توقع الحرارة يجيب عن سؤال تنبؤ ويمكن أن يدخل متحكمًا؛ التنبؤ وحده لا يختار الفعل. MPC وتقليد سياسة معلّمة بدائل، ولا ندعي أن RL ضروري أو أفضل بلا مقارنة.','These are sequential decisions whose effects depend on state, thermal memory and cumulative reward. A temperature predictor answers a forecasting question and can form part of a controller; prediction alone does not choose an action. MPC and imitation of a labelled policy are alternatives. We do not claim RL is necessary or better without a comparison.'))}</p><a href="https://spinningup.openai.com/en/latest/spinningup/rl_intro.html" target="_blank" rel="noreferrer">{ui(t('أساس حلقة الوكيل والمكافأة المتراكمة','Agent loop and cumulative reward foundation'))} · OpenAI Spinning Up</a></details>
 <details data-testid="decision-viva"><summary>{ui(t('أسئلة المناقشة','Viva questions'))}</summary>{[
 ['لو توقعنا الحرارة فقط، من سيختار الشرارة والمروحة؟','If we only predict temperature, who chooses spark and fan?',2,'policy','agent'],
 ['هل خفض مؤشر الضرر 12% يعني عمرًا أطول 12%؟','Does 12% lower damage index mean 12% longer life?',4,'thermal','damage'],
 ['هل reward قراءة حساس مستقلة أم تصميم أهداف من البيئة والمرجع؟','Is reward an independent sensor reading or objectives designed from environment and reference?',4,'reward','policy_reward'],
 ].map(([ar,en,s,r,id])=><div key={String(id)}><p>{ui(t(String(ar),String(en)))}</p><button type="button" onClick={()=>{onStage(Number(s));onRole(r as ControllerRole);onSelect(String(id));}}>{ui(t('افتح المرحلة والمصدر','Open stage and source'))}</button></div>)}</details>
 </section>;
}

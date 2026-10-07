import { useUI } from './useUI';
import { format } from './types';
import { turboFlowData } from './model/turbo-layout.mjs';

export const flowSteps = [
  { label:'هواء الدخول', title:'يدخل الهواء إلى الضاغط', part:'compressor', concept:'air', hint:'المسار الأزرق يوضح دخول الهواء. معدّل الكتلة المعروض محسوب من نقطة تشغيل المحرك.' },
  { label:'الضاغط', title:'يدفع الضاغط الشحنة نحو المحرك', part:'compressor', concept:'map', hint:'يرفع الضاغط ضغط الهواء قبل وصوله إلى الأسطوانات. ضغط السحب هنا مدخل مستقل للمحاكي، وليس نتيجة محاكاة دوران التيربو.' },
  { label:'العمود', title:'عمود واحد ينقل الطاقة', part:'turbo-shaft', concept:'turbocharger', hint:'ينقل العمود دوران التوربين إلى الضاغط ميكانيكيًا. يبقى الهواء والعادم في مسارين منفصلين.' },
  { label:'التوربين', title:'العادم القادم من المحرك يدير التوربين', part:'turbine', concept:'egt', hint:'المسار البرتقالي يوضح غاز العادم. حرارته من حسابات المحرك؛ حركة ريش التوربين مبطّأة للتعلّم.' },
  { label:'خروج العادم', title:'يغادر الغاز نحو نظام العادم', part:'turbine', concept:'exhaust_flow', hint:'كتلة العادم في النموذج تساوي الهواء والوقود الداخلين. المسار هنا توضيحي؛ لا يعرض محاكاة CFD.' },
] as const;

export function FlowGuide({frame,step,onStep}:{frame:any;step:number;onStep:(index:number)=>void}) {
  const { format, ui } = useUI();

  const flow=turboFlowData(frame);
  return <div className="studio-flow-guide" aria-label={ui("تتبّع مساري التيربو")}>
    <div className="studio-flow-guide__head"><button className={step<0?"active":""} aria-pressed={step<0} onClick={()=>onStep(-1)}>{ui("عرض المسارين")}</button><span className="studio-flow-values"><span className="air-value">{ui("هواء ")}<bdi dir="ltr">{ui(format(flow.air,1))} g/s</bdi></span><span className="exhaust-value">{ui("عادم ")}<bdi dir="ltr">{ui(format(flow.exhaust,1))} g/s</bdi></span></span></div>
    <div className="studio-flow-shortcuts">{flowSteps.map((item,index)=><button key={item.label} aria-pressed={step===index} className={step===index?'active':''} onClick={()=>onStep(index)}><span>{ui(index+1)}</span>{ui(item.label)}</button>)}</div>
    <p>{ui("الأزرق: هواء إلى المحرك · البرتقالي: عادم منه · حركة الجسيمات تمثّل معدّل الكتلة على مقياس مبطّأ.")}</p>
  </div>;
}

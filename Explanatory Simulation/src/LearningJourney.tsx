import { usePreferences } from './Preferences';
import type { Ref } from 'react';

type Props = { layer: string; onLayer: (layer: string) => void; onShowModel: () => void; modelReady: boolean; showModelRef: Ref<HTMLButtonElement> };

/** A teaching map: opens existing scenes without creating or advancing an episode. */
export default function LearningJourney({ layer, onLayer, onShowModel, modelReady, showModelRef }: Props) {
  const { t } = usePreferences();
  const steps = [
    {
      id: 'vehicle', label: t('دخول الهواء وخروج العادم', 'Air in, exhaust out'),
      flow: t('هواء الخارج يمر بالفلتر والضاغط والمبرّد والخانق إلى الأسطوانات. العادم يخرج عبر التوربين إلى مؤخرة السيارة.', 'Outside air passes through the filter, compressor, intercooler and throttle into the cylinders. Exhaust leaves through the turbine and the rear of the car.'),
      connection: t('ابدأ بتتبّع المسارين في السيارة؛ كتلة الهواء الداخلة تربط السحب بالوقود والعزم.', 'Trace both paths in the car first; incoming air mass connects intake to fuel and torque.'),
      question: t('أشر إلى مكان دخول الهواء ومكان خروج العادم. أين ينتهي مسار السحب ويبدأ مسار العادم؟', 'Point to the air inlet and exhaust outlet. Where does the intake path end and the exhaust path begin?'),
    },
    {
      id: 'engine', label: t('الاحتراق والعزم', 'Combustion and torque'),
      flow: t('يدخل الهواء والوقود، ويضغط المكبس الشحنة، ثم يدفعه الاحتراق. تصل الحركة إلى عمود المرفق وتخرج غازات ساخنة في شوط العادم.', 'Air and fuel enter, the piston compresses the charge, then combustion pushes it down. Motion reaches the crankshaft and hot gas leaves during the exhaust stroke.'),
      connection: t('العزم والوقود وحرارة العادم نواتج مرتبطة؛ غيّر مدخلًا واحدًا في المحرك وافحص الثلاثة معًا.', 'Torque, fuel and exhaust temperature are connected outputs; change one engine input and inspect all three together.'),
      question: t('اشرح كيف يصل أثر الشرارة أو لامدا إلى العزم وغاز العادم. هل كل تغيير يحسّن جميع النواتج؟', 'Explain how spark or lambda affects torque and exhaust gas. Does every change improve all outputs?'),
    },
    {
      id: 'turbo', label: t('التيربو ومسارا الغاز', 'Turbo and both gas paths'),
      flow: t('يمر العادم الساخن بالتوربين فيدير العمود المشترك والضاغط. يبقى هواء السحب والعادم في مسارين منفصلين؛ ويبرّد مبرد الشحنة الهواء بعد الضاغط.', 'Hot exhaust passes through the turbine and drives the shared shaft and compressor. Intake air and exhaust stay on separate paths; the intercooler cools air after the compressor.'),
      connection: t('اتبع انتقال الطاقة من العادم إلى ضغط السحب، ثم افصل حرارة الغاز عن حرارة غلاف التوربين.', 'Follow energy from exhaust to intake pressure, then distinguish gas temperature from turbine housing temperature.'),
      question: t('كيف ينقل التيربو الطاقة بين المسارين دون أن يخلط الهواء والعادم؟', 'How does the turbo transfer energy between the two paths without mixing air and exhaust?'),
    },
    {
      id: 'thermal', label: t('الحرارة وذاكرتها', 'Heat and thermal memory'),
      flow: t('تنتقل الطاقة إلى معدن المحرك والزيت وغلاف التوربين وتخرج عبر مسارات التبريد. تتغير حرارة الغاز بسرعة، بينما يحتفظ المعدن بالحرارة.', 'Energy reaches engine metal, oil and turbine housing, then leaves through cooling paths. Gas temperature changes quickly while metal retains heat.'),
      connection: t('جرّب التسخين ثم التبريد. المروحة والمضخة تؤثران في مسارات الكتلة والزيت؛ يتبادل غلاف التوربين الحرارة مع الغاز والجو.', 'Try heating, then cooling. Fan and pump affect the block and oil paths; turbine housing exchanges heat with gas and ambient air.'),
      question: t('لماذا قد يبقى غلاف التيربو ساخنًا بعد انخفاض حرارة العادم؟ وكيف يغيّر ذلك توقيت قرار المشرف؟', 'Why can the turbo housing stay hot after exhaust temperature falls? How does that affect when the supervisor should act?'),
    },
    {
      id: 'agent', label: t('الرؤية وقرار المشرف', 'Preview and supervisor decision'),
      flow: t('يدخل ميل الطريق القادم وحالة المحرك إلى المشرف. يطلب خمسة أوامر، ثم تطبّقها ECU ضمن حدود المصدر ونرى أثر الخطوة في العزم والوقود والحرارة.', 'Road preview and engine state enter the supervisor. It requests five commands, then the ECU applies them within source limits and we inspect the step’s torque, fuel and thermal response.'),
      connection: t('هذه تجربة قصيرة لفهم الفكرة: هل تساعد معلومات المستقبل على الموازنة بين تتبّع العزم والوقود ومؤشر الضرر؟ المعاينة هنا من مسار التجربة.', 'This is a short experiment to understand the idea: can future information help balance torque tracking, fuel and the damage proxy? Preview here comes from the experiment’s road.'),
      question: t('قبل الصعود، ما المعلومات التي يقرأها المشرف؟ وما الأمر الذي تغيّر، وما أثره؟ فرّق بين هدف السياسة والنتيجة التي شاهدتها.', 'Before the climb, what does the supervisor read? Which command changed, and what followed? Distinguish the policy objective from the outcome you observed.'),
    },
  ];
  const active = steps.find(step => step.id === layer) || steps[0];
  return <section className="project-mission learning-journey" aria-label={t('رحلة فهم المشروع', 'Project learning journey')}>
    <p className="learning-journey__purpose"><strong>{t('مختبر شرح تفاعلي', 'Interactive learning lab')}</strong> · {t('افهم الآلية، جرّب تغييرًا، ثم اربطه بفكرة المشروع.', 'Understand the mechanism, try a change, then connect it to the project idea.')}</p>
    <p>{t('فكرة المشروع: مشرف يوازن تتبّع العزم والوقود ومؤشر الضرر، مستفيدًا من معرفة ميل الطريق القادم.', 'Project idea: a supervisor balances torque tracking, fuel and the damage proxy using knowledge of the road ahead.')}</p>
    <nav aria-label={t('أجزاء رحلة الشرح', 'Learning journey parts')}><ol>{steps.map((step, index) => <li key={step.id}><button type="button" aria-current={layer === step.id ? 'step' : undefined} onClick={() => onLayer(step.id)}><span>{index + 1}</span>{step.label}</button></li>)}</ol></nav>
    <details className="learning-journey__connection">
      <summary>{t('افهم هذا الرابط: ', 'Understand this connection: ')}{active.label}</summary>
      <p><strong>{t('ما يدخل ويخرج:', 'Inputs and outputs:')}</strong> {active.flow}</p>
      <p><strong>{t('صلته بالمشروع:', 'Connection to the project:')}</strong> {active.connection}</p>
      <p><strong>{t('اختبر فهمك قبل الانتقال:', 'Check your understanding before moving on:')}</strong> {active.question}</p>
    </details>
    <button ref={showModelRef} className="learning-journey__show primary" type="button" disabled={!modelReady} onClick={onShowModel}>{t('شاهد الجزء في النموذج', 'Show this part in the model')}</button>
  </section>;
}

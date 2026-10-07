import { useUI } from './useUI';
import { useState } from 'react';
import { usePreferences } from './Preferences';
import { pressurePoints, pressureReading } from './model/pressure.mjs';
import type { Frame, Source } from './types';
import './pressure.css';
export function PressureDiagram({ frame, sessionId, onSource }: { frame?: Frame|null; sessionId:string; onSource:(source:Source)=>void }) {
  const { ui } = useUI();

  const { t, direction } = usePreferences();
  const [selected, setSelected] = useState('atmosphere');
  const points = pressurePoints(frame, sessionId);
  const point = points.find(item=>item.id===selected)!;
  const input = pressureReading(frame,sessionId);
  const labels = [t('الجو الخارجي','External atmosphere'),t('الضاغط / المبرد','Compressor / intercooler'),t('قبل الخانق','Before throttle'),t('مجمع السحب بعد الخانق','Manifold after throttle')];
  const descriptions = [
    t('مدخل السيناريو p_baro من الخانة 10 عند زمن دخل القرار. يمر إلى كثافة الجو ثم Vehicle.demand لطلب الطريق. مولدات الطريق تثبته عند 101.3؛ الارتفاع غير محاكى.','Scenario p_baro from slot 10 at decision input time. It feeds ambient density and then Vehicle.demand for road demand. Road generators fix it at 101.3; altitude is not modeled.'),
    t('لا توجد قراءة ضغط لهذه المحطة. استدعاء سقف الضاغط في البيئة لا يمرر p_baro؛ يستخدم وسيط ضغط المدخل الافتراضي 99.3 kPa. هذا ثابت الدالة وليس قياسًا لهذه المحطة.','No pressure reading is available at this station. The environment compressor-ceiling call does not pass p_baro; it uses the default inlet-pressure parameter of 99.3 kPa. This is a function default, not a station measurement.'),
    t('قناتا الضغط في سجل السيارة تقعان قبل الخانق، رغم اسم إحداهما. لا توجد عينة سجل محملة هنا؛ لا تُنقل قراءتهما تلقائيًا إلى MAP بعد الخانق.','Both vehicle log pressure channels sit before the throttle despite one channel name. No log sample is loaded here; their readings must not be assigned automatically to post-throttle MAP.'),
    t('map_kpa هو ضغط مطلق محاكى بعد الخانق عند نهاية الإطار؛ ليس قناة ضغط مقاسة من السيارة. الفرق عن ضغط دخل السيناريو معروض للمقارنة بين زمنين موضحين.','map_kpa is modeled absolute pressure after the throttle at frame end; it is not a measured vehicle pressure channel. Its difference from scenario input pressure compares the two labeled times.'),
  ];
  const i = points.indexOf(point);
  const number = (value:number|null) => value === null ? t('غير متاح','Unavailable') : value.toFixed(1);
  const sources:Source[] = [{file:'engine_env.py',line:800,variable:'obs_in[10]'},{file:'engine_env.py',line:774,variable:'boost_ceiling_kpa'},{file:'REFERENCES.md',line:431,variable:'pressure sensor location'},{file:'engine_env.py',line:921,variable:'map_kpa'}];
  return <section className="pressure-diagram" dir={direction} data-testid="pressure-diagram"><h4>{ui(t('أين يقع الضغط؟','Where is the pressure?'))}</h4><div className="pressure-path" role="group" aria-label={ui(t('مسار الهواء ومواقع الضغط','Air path and pressure locations'))}>{points.map((item,index)=><button key={item.id} data-pressure-point={item.id} aria-pressed={selected===item.id} className={selected===item.id?'selected':''} onClick={()=>setSelected(item.id)}>{ui(labels[index])}<small>{ui(index===0?t('مدخل السيناريو','Scenario input'):index===3?t('محاكاة','Modeled'):t('بدون قراءة','No reading'))}</small></button>)}</div><div className="pressure-detail" aria-live="polite"><strong>{ui(labels[i])}</strong><p>{ui(descriptions[i])}</p><p><bdi dir="ltr">{ui(number(point.value))} kPa abs</bdi>{point.timeS!==null && <> · <bdi dir="ltr">{ui(point.timeS.toFixed(1))} s</bdi> · {ui(i===0?t('زمن الدخل','Input time'):t('زمن النهاية','End time'))}</>}</p>{point.gaugeKpa!==null && <p><bdi dir="ltr">{ui(number(point.gaugeKpa))} kPa gauge</bdi> · {ui(t('نسبةً إلى ضغط دخل السيناريو','Relative to scenario input pressure'))}</p>}<code dir="ltr">{i===0?'p_baro = obs_in[10] × 8 + 101.3':i===3?'p_gauge = map_kpa − p_baro':'—'}</code>{i===0 && <p>{ui(t('القيمة المطبعة','Normalized value'))}: <bdi dir="ltr">{ui(input.normalized===null?number(null):input.normalized.toFixed(3))}</bdi></p>}<button onClick={()=>onSource(sources[i])}>{ui(t('مصدر هذا الموقع','Source for this location'))}</button>{i===0 && <button onClick={()=>onSource({file:'engine_env.py',line:874,variable:'rho → Vehicle.demand'})}>{ui(t('مسار كثافة الجو وطلب الطريق','Ambient density and road demand route'))}</button>}</div><p className="subtle">{ui(t('المطلق مرجعه الفراغ؛ القياسي هو المطلق ناقص ضغط الجو. اسم القناة لا يحدد موقع حساسها.','Absolute pressure is referenced to vacuum; gauge pressure is absolute minus atmosphere. A channel name does not establish its sensor location.'))}</p></section>;
}


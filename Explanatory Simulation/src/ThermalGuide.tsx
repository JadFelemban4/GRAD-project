import { useUI } from './useUI';
import { Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { thermalLesson, thermalAnchors, thermalNames } from './model/thermal-flow.mjs';
import type { ThermalPath } from './model/thermal-flow.mjs';
import { format } from './types';
type ThermalProps = {
  frame: any;
  focus: string;
  onSelect: (id: string) => void;
};

function EnergyPath({ path }: { path: ThermalPath }) {
  const a = thermalAnchors[path.from];
  const b = thermalAnchors[path.to];
  const mid: [number, number, number] = [
    (a[0] + b[0]) / 2,
    Math.max(a[1], b[1]) + .3,
    (a[2] + b[2]) / 2,
  ];
  const end = new THREE.Vector3(...b);
  const direction = end.clone().sub(new THREE.Vector3(...mid)).normalize();
  const rotation = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0), direction,
  );
  return <group>
      <Line points={[a,mid,b]} color="#cc9aff" lineWidth={3} dashed dashSize={.07} gapSize={.045}/>
      <mesh position={end.clone().addScaledVector(direction,-.065)} quaternion={rotation}>
      <coneGeometry args={[.06,.14,8]}/>
      <meshBasicMaterial color="#cc9aff"/>
      </mesh>
      </group>;
}

export function ThermalEnergyPaths({ frame, focus, onSelect }: ThermalProps){
  const { ui } = useUI();

  const lesson = thermalLesson(frame, focus);
  const activePaths = lesson.paths.filter(p => p.state === 'active');
  const labels = [lesson.node, ...new Set(activePaths.flatMap(p => [p.from, p.to]))]
    .filter((id, i, all) => all.indexOf(id) === i);
  const concepts: Record<string, string> = {
    gas: 'egt', ambient: 'ambient_temp', radiator: 'fan_duty', rpm: 'rpm',
  };

  return (
    <group>
      {activePaths.map(p => <EnergyPath key={p.id} path={p}/>)}
      {labels.map(id => (
        <Html key={id} position={thermalAnchors[id]} center zIndexRange={[2, 0]}>
          <button className="thermal-anchor" onClick={() => onSelect(concepts[id] || id)}>
            {ui(thermalNames[id])}
          </button>
        </Html>
      ))}
    </group>
  );
}

export function ThermalGuide({ frame, focus, onSelect }: ThermalProps){
  const { format, ui, uiTemplate, direction } = useUI();

  const lesson = thermalLesson(frame, focus);
  const f = frame || {};
  return <section className="thermal-guide" aria-label={ui("أسباب الحرارة ومساراتها")} dir={direction}>
      <div className="thermal-guide__nodes">{['t_block','t_oil','t_turb'].map(id=>
      <button key={id} aria-pressed={lesson.node===id} onClick={()=>onSelect(id)}>{ui(thermalNames[id])}</button>)}</div>
      <strong>{ui(thermalNames[lesson.node])} · <bdi dir="ltr">{ui(format(typeof f[lesson.node]==='number'?f[lesson.node]-273.15:null))} °C</bdi>
      </strong>
      <p>{lesson.paths.map(p => (
        <span key={p.id}>
          {ui(p.state === 'active'
            ? uiTemplate("من {0} إلى {1}", "From {0} to {1}", thermalNames[p.from], thermalNames[p.to])
            : p.state === 'equal'
              ? uiTemplate("{0} / {1}: حرارة متساوية", "{0} / {1}: equal temperature", thermalNames[p.from], thermalNames[p.to])
              : p.state === 'inactive'
                ? p.id === 'radiator'
                  ? 'الكتلة وسائل التبريد / الرديتر: المسار غير نشط؛ منظم النموذج مغلق'
                  : uiTemplate("{0} / {1}: المسار غير نشط", "{0} / {1}: path inactive", thermalNames[p.from], thermalNames[p.to])
                : uiTemplate("{0} / {1}: غير متاح", "{0} / {1}: unavailable", thermalNames[p.from], thermalNames[p.to]))}
        </span>
      ))}</p>
      <small>{ui("غاز أزرق/برتقالي · سائل أزرق/ذهبي · طاقة بنفسجية متقطعة؛ الأسهم انتقال طاقة وليست أنابيب.")}</small>
      <details>
      <summary>{ui("الزمن والمنظم ومصادر النموذج")}</summary>
      <p>{ui(f.phase
          ? ui('تجربة حرارية مستقلة · ') + ui(({
              start: 'البداية', heating: 'تسخين', cooling: 'تبريد',
            } as Record<string, string>)[f.phase])
          : 'جلسة الطريق')} {ui(" · حرارة العينة المعروضة عند ")}<bdi>{ui(format(f.time_s))} s</bdi>{ui(". بعد البداية، الغاز ومدخل الوقود والدوران يخصّان فترة الحساب السابقة؛ الاتجاه المعروض مقارنة حدود الغاز وحرارة النهاية، وليس قياس تدفق حراري لحظي.")}</p>
      <p>{ui("منظم حراري بديل في النموذج: يتجاوز الرديتر تحت منطقة الفتح، ويتدرج تأثير المروحة والمضخة مع الفتح. آخر فتح محسوب قبل آخر تحديث حرارة (0.1 s في التجربة؛ خطوة الطريق في الجلسة): ")}<bdi>{ui(format(lesson.regulator===null?null:lesson.regulator*100))}%</bdi>{ui(". نظام B58 الفعلي لإدارة الحرارة مختلف.")}</p>
      <p>{ui(lesson.node === 't_turb'
          ? 'التوربين يتبادل مع الغاز والجو فقط؛ لا وصلة تبريد مباشرة من المروحة أو المضخة.'
          : 'الوقود مصدر للكتلة والزيت؛ الزيت يستقبل أيضًا احتكاك الدوران وتحريكه. تبادل الزيت والكتلة ينعكس مع فرق الحرارة.')} {ui(f.phase === 'cooling'
          ? 'أزيل الوقود والعادم؛ حد الغاز هو الجو، لكن دوران 800 RPM يبقى وقد ينتج حرارة زيت.'
          : '')}</p>
      <p>
      <code>thermal.py · ThermalNetwork.step</code> {ui(" · ثلاث عقد مجمعة ومسارات تعليمية، لا مخطط تبريد مصنعي ولا قيم واط.")}</p>
      </details>
      </section>;
}


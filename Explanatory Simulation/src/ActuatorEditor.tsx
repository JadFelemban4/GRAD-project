import { useUI } from './useUI';
import { editDraft, editorPresentation, referenceDraft } from './model/supervisor.mjs';
import { format } from './types';
import type { Meta } from './types';

type Props = {
  actions: Meta['actions'];
  draft: number[];
  onChange: (next: number[]) => void;
  activePolicy: string;
  comparison: boolean;
  busy: boolean;
};

export default function ActuatorEditor({ actions, draft, onChange, activePolicy, comparison, busy }: Props) {
  const { format, ui, uiTemplate, direction } = useUI();

  const presentation = editorPresentation(activePolicy, comparison, busy);
  if (!presentation.showEditor) return <p className="actuator-editor subtle" dir={direction}>{ui(presentation.message)}</p>;

  return <fieldset className="actuator-editor" disabled={presentation.disabled}>
    <legend>{ui("مسودة الأوامر للخطوة التالية")}</legend>
    <div className="slider-grid">
      {actions.map((action, index) => <label key={action.id}>
        <span>{ui(action.name)} <bdi dir="ltr">{ui(format(draft[index], 2))} {ui(action.unit)}</bdi></span>
        <input
          aria-label={ui(uiTemplate("مسودة {0}", "Draft {0}", action.name))}
          type="range"
          min={action.lo}
          max={action.hi}
          step={index === 1 ? .01 : index >= 3 ? .05 : .5}
          value={draft[index]}
          onChange={event => onChange(editDraft(draft, index, +event.target.value, action))}
        />
        <small dir="ltr">{ui(action.lo)}…{ui(action.hi)} {ui(action.unit)} · ≤ {ui(action.slew)} {ui(action.slew_unit)}</small>
      </label>)}
    </div>
    <button type="button" onClick={() => onChange(referenceDraft())}>{ui("صفّر التعديلات · مروحة ومضخة بكامل التشغيل")}</button>
    <p className="subtle">{ui("مسودة معلّقة حتى تنفيذ الخطوة التالية؛ تعديلها لا يغيّر زمن الجلسة. القراءات أعلاه تخص العينة المختارة.")}</p>
    {comparison && <p>{ui("المقارنة تمنع التحرير اليدوي.")}</p>}
  </fieldset>;
}

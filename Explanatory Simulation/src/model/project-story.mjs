export const PREVIEW_HORIZONS_S = Object.freeze([2, 5, 15, 30]);

export const PHYSICAL_CONTROLS = Object.freeze([
  Object.freeze({ id: 'spark_trim', index: 0, label: 'تعديل توقيت الشرارة', unit: '°BTDC', digits: 1 }),
  Object.freeze({ id: 'lambda_trim', index: 1, label: 'تعديل لامدا', unit: 'λ', digits: 2 }),
  Object.freeze({ id: 'boost_trim', index: 2, label: 'تعديل ضغط المانيفولد', unit: 'kPa', digits: 1 }),
  Object.freeze({ id: 'fan_duty', index: 3, label: 'أمر مروحة الرديتر', unit: 'fraction', digits: 2 }),
  Object.freeze({ id: 'pump_duty', index: 4, label: 'أمر مضخة التبريد', unit: 'fraction', digits: 2 }),
]);

const finiteOrNull = value => typeof value === 'number' && Number.isFinite(value) ? value : null;

function sampleRoad(road, inputTime, horizon) {
  if (!Array.isArray(road?.time_s) || !Array.isArray(road?.grade_pct) || road.time_s.length === 0 || road.time_s.length !== road.grade_pct.length) return null;
  const target = inputTime + horizon;
  let selected = -1;
  for (let i = 0; i < road.time_s.length; i++) {
    if (!Number.isFinite(road.time_s[i]) || !Number.isFinite(road.grade_pct[i])) continue;
    if (road.time_s[i] <= target + 1e-9) selected = i;
    else break;
  }
  if (selected < 0) {
    for (let i = 0; i < road.grade_pct.length; i++) if (Number.isFinite(road.grade_pct[i])) return road.grade_pct[i];
    return null;
  }
  return road.grade_pct[selected];
}

export function buildProjectStory(frame, { preview = true, road, time = 0, previousFrame, sessionId, previousSessionId } = {}) {
  const currentGradePct = finiteOrNull(frame?.grade_pct);
  const inputTime = finiteOrNull(frame?.input_time_s) ?? finiteOrNull(frame?.time_s) ?? finiteOrNull(time) ?? 0;
  const endTime = finiteOrNull(frame?.time_s) ?? inputTime;
  const hasAppliedAction = Array.isArray(frame?.action) && frame.action.length === 5 && frame.action.every(value=>finiteOrNull(value)!==null) && Array.isArray(frame?.command) && frame.command.length === 5 && frame.command.every(value=>finiteOrNull(value)!==null) && endTime > inputTime;
  let futureGrades;
  if (!preview) {
    futureGrades = PREVIEW_HORIZONS_S.map(() => 0);
  } else if (Array.isArray(frame?.preview_pct) && frame.preview_pct.length === PREVIEW_HORIZONS_S.length && frame.preview_pct.every(value => Number.isFinite(value))) {
    futureGrades = [...frame.preview_pct];
  } else {
    futureGrades = PREVIEW_HORIZONS_S.map(horizon => sampleRoad(road, inputTime, horizon));
  }

  const command = hasAppliedAction ? frame.command : [];
  const egtC = hasAppliedAction ? finiteOrNull(frame?.egt_c) : null;
  const turbineC = finiteOrNull(frame?.t_turb) === null ? null : finiteOrNull(frame.t_turb) - 273.15;
  const previousMatches = hasAppliedAction && !!sessionId && sessionId === previousSessionId && finiteOrNull(previousFrame?.time_s) === inputTime;
  const memory = [['t_block', 'معدن المحرك'], ['t_oil', 'الزيت'], ['t_turb', 'حاوية التوربين']].map(([id,label]) => {
    const beforeK = previousMatches ? finiteOrNull(previousFrame?.[id]) : null;
    const afterK = finiteOrNull(frame?.[id]);
    return {id,label,beforeC:beforeK === null ? null : beforeK-273.15,afterC:afterK === null ? null : afterK-273.15,deltaC:beforeK === null || afterK === null ? null : afterK-beforeK};
  });
  const observedDemand = finiteOrNull(frame?.obs_in?.[18]);
  return {
    observedTorqueReqNm: observedDemand === null ? null : (observedDemand+1)*200,
    outputs: Object.fromEntries(['torque_req','torque','mdot_fuel','mdot_air','egt_c'].map(key=>[key,hasAppliedAction ? finiteOrNull(frame?.[key]) : null])),
    torqueErrorNm:hasAppliedAction && finiteOrNull(frame?.torque)!==null && finiteOrNull(frame?.torque_req)!==null ? frame.torque-frame.torque_req : null,
    memory, previousMatches,
    damageRate:hasAppliedAction ? finiteOrNull(frame?.damage_rate) : null,
    totalDamage:finiteOrNull(frame?.totals?.damage),
    reward:hasAppliedAction ? finiteOrNull(frame?.reward) : null,
    rewardFields:Object.fromEntries(['r_resp','r_fuel','r_life','cost_torque','cost_knock','cost_egt'].map(key=>[key,hasAppliedAction ? finiteOrNull(frame?.[key]) : null])),
    currentGradePct,
    inputTimeS: inputTime,
    previewSlots: PREVIEW_HORIZONS_S.map((seconds, index) => ({ seconds, gradePct: finiteOrNull(futureGrades[index]) })),
    torqueReqNm: finiteOrNull(frame?.torque_req),
    egtC,
    turbineC,
    timeline: { inputS: inputTime, endS: endTime, hasAppliedAction, intervalEgtC: egtC, endTurbineC: turbineC },
    controls: PHYSICAL_CONTROLS.map(({ id, index, label, unit, digits }) => ({
      id, label, unit, digits, value: finiteOrNull(command[index]),
    })),
  };
}

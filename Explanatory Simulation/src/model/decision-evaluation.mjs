const finite = v => typeof v==='number' && Number.isFinite(v) ? v : null;
export function relativeReduction(value, reference) { return finite(value)!==null && finite(reference)!==null && reference>0 ? (reference-value)/reference*100 : null; }
export function roleFor(quantity) { if(['spark_trim','lambda_trim','boost_trim','fan_duty','pump_duty','action','agent'].includes(quantity))return 'policy'; if(['torque','engine_torque','mdot_fuel','fuel','egt_c','egt'].includes(quantity))return 'engine'; if(['t_turb','t_oil','t_block'].includes(quantity))return 'thermal'; return 'reward'; }
export function roleSequence(story) { return story.timeline.hasAppliedAction ? ['policy','ecu','engine','thermal','reward'] : []; }
export function decisionOutcome(frame, story) {
 const applied=story.timeline.hasAppliedAction;
 const get=k=>applied?finite(frame?.[k]):null;
 const base=k=>applied?finite(frame?.baseline?.[k]):null;
 const demand=story.outputs.torque_req, torque=story.outputs.torque;
 const errorNm=demand===null||torque===null?null:torque-demand;
 const weights=[20,21,22].map(i=>finite(frame?.obs_in?.[i]));
 const terms=['r_resp','r_fuel','r_life'].map(get);
 const weightedSubtotal=weights.every(v=>v!==null)&&terms.every(v=>v!==null)?terms.reduce((s,v,i)=>s+v*weights[i],0):null;
 const uncertainty=get('reward_uncertainty_penalty'), smoothness=get('reward_smoothness_penalty');
 const complete=weightedSubtotal!==null&&uncertainty!==null&&smoothness!==null;
 return {demand,torque,errorNm,errorPct:errorNm!==null&&demand>0?errorNm/demand*100:null,baselineTorque:base('torque'),fuel:get('mdot_fuel'),baselineFuel:base('mdot_fuel'),fuelReductionPct:relativeReduction(get('mdot_fuel'),base('mdot_fuel')),damageRate:story.damageRate,baselineDamageRate:base('damage_rate'),intervalDamage:story.damageRate===null?null:story.damageRate*(story.timeline.endS-story.timeline.inputS),totalDamage:story.totalDamage,baselineTotalDamage:finite(frame?.totals?.damage_base),damageReductionPct:relativeReduction(story.totalDamage,finite(frame?.totals?.damage_base)),totalFuel:finite(frame?.totals?.fuel_g),baselineTotalFuel:finite(frame?.totals?.fuel_base_g),weights,terms,weightedSubtotal,uncertainty,smoothness,complete,reconstructed:complete?weightedSubtotal-uncertainty-smoothness:null,reward:story.reward};
}

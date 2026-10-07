import { vehicleTurboAnchors } from './vehicle-airflow.mjs';

export const thermalAnchors = Object.freeze({
  t_block: [1.49, .85, -.06],
  t_oil: [1.49, .5, -.06],
  t_turb: vehicleTurboAnchors.turbine,
  fuel: [.75, 1.7, -.6],
  rpm: [.8, .35, -.7],
  gas: [2.1, 1.65, .75],
  ambient: [3.4, 1.6, -.8],
  radiator: [2.82, .83, 0],
});

export const thermalNames = Object.freeze({
  t_block: 'الكتلة وسائل التبريد',
  t_oil: 'الزيت',
  t_turb: 'التوربين',
  fuel: 'طاقة الوقود',
  rpm: 'احتكاك ودوران الزيت',
  gas: 'حد الغاز',
  ambient: 'الجو',
  radiator: 'الرديتر',
});

const finite = v => typeof v === 'number' && Number.isFinite(v);
const state = v => finite(v) ? (v > 0 ? 'active' : 'inactive') : 'unknown';

export function thermalLesson(frame, selected) {
  const f = frame || {};
  const node = ['t_block', 't_oil', 't_turb'].includes(selected) ? selected : 't_block';
  const paths = [];

  const transfer = (id, a, b, ta, tb, enabled = 'active') => {
    let s = enabled;
    let from = a;
    let to = b;
    if (s === 'active') {
      s = !finite(ta) || !finite(tb) ? 'unknown' : ta === tb ? 'equal' : 'active';
      if (s === 'active' && ta < tb) [from, to] = [b, a];
    }
    paths.push({ id, from, to, state: s });
  };
  const source = (id, a, b, v) => paths.push({ id, from: a, to: b, state: state(v) });
  const ambient = finite(f.ambient_c) ? f.ambient_c + 273.15 : null;

  if (node === 't_block' || node === 't_oil') {
    source('fuel', 'fuel', node, f.mdot_fuel);
    transfer('exchange', 't_block', 't_oil', f.t_block, f.t_oil);
    transfer('ambient', node, 'ambient', f[node], ambient);
    if (node === 't_block') {
      transfer('radiator', node, 'radiator', f[node], ambient, state(f.thermostat));
    } else {
      source('rpm', 'rpm', node, finite(f.rpm) ? (f.rpm > 400 ? f.rpm : 0) : null);
    }
  } else {
    const gas = finite(f.exhaust_boundary_c) ? f.exhaust_boundary_c : f.egt_c;
    transfer('gas', 'gas', node, finite(gas) ? gas + 273.15 : null, f.t_turb);
    transfer('ambient', node, 'ambient', f.t_turb, ambient);
  }

  return { node, paths, regulator: finite(f.thermostat) ? f.thermostat : null };
}

// The turbine node of thermal.py on its own, for the housing-lag figure.
// ThermalNetwork._substep advances t_turb with three lines that read no other
// node (no block, no oil), so the node can run alone. These functions repeat
// those lines in the same order, so the figure draws the project's numbers;
// housing-lag.test.mjs checks them against a run of ThermalNetwork itself
// (figures/housing-lag/params.json, written by export_params.py).

// τ = C / UA: the time to cover 63 % of a step. For this node UA is the gas
// side, which grows with exhaust flow (floored as thermal.py floors it), plus
// the loss to ambient.
export function tauOf(turbine, mdotExhGps) {
  return turbine.c_turb / (turbine.ua_gas_turb * Math.max(mdotExhGps, turbine.mdot_floor_gps) + turbine.ua_turb_amb);
}

// Where the housing settles for a held input: the gas heats it and ambient
// cools it, so it settles between the two, not at the gas temperature.
export function settleOf(turbine, mdotExhGps, egtK, tAmbK) {
  const uaGt = turbine.ua_gas_turb * Math.max(mdotExhGps, turbine.mdot_floor_gps);
  return (uaGt * egtK + turbine.ua_turb_amb * tAmbK) / (uaGt + turbine.ua_turb_amb);
}

// One call of ThermalNetwork.step for this node: dt split into equal explicit
// Euler sub-steps of at most dt_sub_max, inputs held over the call.
export function stepHousing(turbine, tTurbK, dt, mdotExhGps, egtK, tAmbK) {
  const count = Math.max(1, Math.ceil(dt / turbine.dt_sub_max - 1e-9));
  const h = dt / count;
  let t = tTurbK;
  for (let index = 0; index < count; index++) {
    const uaGt = turbine.ua_gas_turb * Math.max(mdotExhGps, turbine.mdot_floor_gps);
    const qIn = uaGt * (egtK - t);
    const qOut = turbine.ua_turb_amb * (t - tAmbK);
    t += h * (qIn - qOut) / turbine.c_turb;
  }
  return t;
}

// The two burner states, as /api/thermal feeds them: lit is the engine point;
// off is no flow with the gas at ambient (its cooling phase).
export function inputsOf(params, lit) {
  const tAmbK = params.point.ambient_c + 273.15;
  return lit
    ? { mdotExhGps: params.engine.mdot_exh_gps, egtK: params.engine.egt_c + 273.15, tAmbK }
    : { mdotExhGps: 0, egtK: tAmbK, tAmbK };
}
